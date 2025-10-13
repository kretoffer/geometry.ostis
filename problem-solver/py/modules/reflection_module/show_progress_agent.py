import logging
from typing import List, Tuple
from sc_client.models import ScAddr, ScTemplate
from sc_client.constants import sc_type
from sc_client.client import search_by_template

from sc_kpm import ScAgentClassic, ScResult
from sc_kpm.utils import (
    generate_link,
    get_link_content_data
)
from sc_kpm.utils.action_utils import create_action_result
from sc_kpm.utils.action_utils import (
    finish_action_with_status,
    get_action_arguments
)
from sc_kpm import ScKeynodes
from sc_kpm.sc_sets import ScSet

from .additions import get_self_rating, get_system_rating


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s", datefmt="[%d-%b-%y %H:%M:%S]"
)


class ShowProgressAgent(ScAgentClassic):
    def __init__(self):
        super().__init__("action_show_progress")
    
    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("ShowProgressAgent finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result
    
    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("ShowProgressAgent started")

        [user] = get_action_arguments(action_node, 1)

        underrated_themes, overrated_themes = self.get_self_rating(user)
        message = ""
        
        studied_themes_names = self.get_themes_names(self.get_themes_from_set(self.get_studied_themes_set(user)))
        overrated_themes_names = self.get_themes_names(overrated_themes)
        underrated_themes_names = self.get_themes_names(underrated_themes)
        
        if len(studied_themes_names) != 0:
            message += "Вы уже изучили следующие темы: \n"
            message += '\n'.join(studied_themes_names)
            message += '\n\n'
        else:
            message += 'На данный момент Вы не изучали никаких новых тем.\n'
        
        if len(overrated_themes_names) != 0:
            message += "Вам стоит отнестись серьёзнее к следующим темам:\n"
            message += '\n'.join(overrated_themes_names)
            message += '\n\n'

        if len(underrated_themes_names) != 0:
            message += "Обратите внимание, что вы хорошо знаете данные темы:\n"
            message += '\n'.join(underrated_themes_names)
            message += '\n\n'

        create_action_result(action_node, generate_link(message))
        return ScResult.OK
        

    def get_self_rating(self, user: ScAddr) -> Tuple[ScAddr, ScAddr]:
        self_rating, system_rating = get_self_rating(user), get_system_rating(user)

        worth_system_themes_set, well_system_themes_set = self.get_worth_studied_themes_set(system_rating, user), self.get_well_studied_themes_set(system_rating, user)
        worth_self_themes_set, well_self_themes_set = self.get_worth_studied_themes_set(self_rating, user), self.get_well_studied_themes_set(self_rating, user)
        
        good_templ = ScTemplate()
        bad_templ = ScTemplate()

        good_templ.triple(
            well_system_themes_set,
            sc_type.VAR_PERM_POS_ARC,
            (sc_type.VAR_NODE, "_theme")
        )
        search_results = search_by_template(good_templ)
        good_themes = [el.get("_theme") for el in search_results]
        good_templ.triple(
            well_self_themes_set,
            sc_type.VAR_PERM_POS_ARC,
            "_theme"
        )
        search_results = search_by_template(good_templ)
        g = [el.get("_theme") for el in search_results]
        good_themes = [el for el in good_themes if el not in g]

        bad_templ.triple(
            worth_system_themes_set,
            sc_type.VAR_PERM_POS_ARC,
           (sc_type.VAR_NODE, "_theme")
        )
        search_results = search_by_template(bad_templ)
        bad_themes = [el.get("_theme") for el in search_results]

        return good_themes, bad_themes
    

    def get_worth_studied_themes_set(self, rating, user):
        return self._get_worth_well_studied_themes_set(rating, user, ScKeynodes.resolve("nrel_worth_studied_themes", sc_type.CONST_NODE_NON_ROLE))
    

    def get_well_studied_themes_set(self, rating, user):
        return self._get_worth_well_studied_themes_set(rating, user, ScKeynodes.resolve("nrel_well_studied_themes", sc_type.CONST_NODE_NON_ROLE))
    

    def _get_worth_well_studied_themes_set(self, rating, user, comp):
        templ = ScTemplate()
        templ.quintuple(
            user,
            (sc_type.VAR_COMMON_ARC, "arc_to_set"),
            (sc_type.VAR_NODE_TUPLE, "themes_set"),
            sc_type.VAR_PERM_POS_ARC,
            comp
        )
        templ.triple(
            rating,
            sc_type.VAR_PERM_POS_ARC,
            "arc_to_set"
        )
        themes_set = search_by_template(templ)[0].get("themes_set")
        return themes_set
    

    def get_themes_names(self, themes: List[ScAddr]) -> List[str]:
        if not themes:
            return []
        themes_names = []

        for theme in themes:
            themeTempl = ScTemplate()
            themeTempl.quintuple(
                theme,
                sc_type.VAR_COMMON_ARC,
                (sc_type.VAR_NODE_LINK, "_link"),
                sc_type.VAR_PERM_POS_ARC,
                ScKeynodes.resolve("nrel_main_idtf", sc_type.CONST_NODE_NON_ROLE)
            )

            search_results = search_by_template(themeTempl)  
            themes_names.append(str(get_link_content_data(search_results[0].get("_link"))))

    
        return themes_names
    
    def get_themes_from_set(self, set: ScAddr) -> List[ScAddr]:
        themes_set = ScSet(set_node=set)
        return list(themes_set.elements_set)
    

    def get_studied_themes_set(self, user: ScAddr) -> ScAddr:
        templ = ScTemplate()
        templ.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE, "_theme_set"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_studied_themes", sc_type.CONST_NODE_NON_ROLE)
        )
        search_results = search_by_template(templ)
        if search_results:
            return search_results[0].get("_theme_set")
        return ScAddr()
