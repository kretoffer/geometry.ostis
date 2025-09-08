import logging
from typing import List
from sc_client.models import ScAddr, ScTemplate, ScLinkContent, ScLinkContentType
from sc_client.constants import sc_type
from sc_client.client import search_by_template, generate_by_template, delete_elements

from sc_kpm import ScAgentClassic, ScResult
from sc_kpm.sc_sets import ScSet
from sc_kpm.utils import (
    generate_connector,
    generate_node,
    get_link_content
)
from sc_kpm.utils.action_utils import (
    finish_action_with_status,
    get_action_arguments
)
from sc_kpm import ScKeynodes



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
        self.logger.info("CompareRatingOfProgressAgent started")

        user = get_action_arguments(action_node, 1)

        self_rating_level, underrated_themes, overrated_themes = self.get_self_rating(user)
        message = self.get_self_rating_discription(self_rating_level)
        if len(message) != 0:
            message += "\n"
        
        studied_themes_names = self.get_themes(self.get_studied_themes_set(user))
        overrated_themes_names = self.get_themes(overrated_themes)
        underrated_themes_names = self.get_themes(underrated_themes)
        
        if len(studied_themes_names) != 0:
            message += "Вы уже изучили следующие темы: "
            message += ', '.join(studied_themes_names)
            message += '\n'
        else:
            message += 'На данный момент Вы не изучали никаких новых тем.\n'
        
        if len(overrated_themes) != 0:
            message += "Вам стоит отнестись серьёзнее к следующим темам: "
            message += ', '.join(overrated_themes_names)
            message += '\n'

        if len(underrated_themes) != 0:
            message += "Обратите внимание, что вы хорошо знаете данные темы: "
            message += ', '.join(underrated_themes_names)
            message += '\n'

        # TODO отобразить сообщение в боте

        return ScResult.OK
        



    def get_self_rating(user: ScAddr) -> tuple[ScAddr, ScAddr, ScAddr]:

        def get_self_rating_params(user: ScAddr, struct: ScAddr, relation: ScAddr) -> ScAddr:
            templ = ScTemplate()
            templ.quintuple(
                user,
                sc_type.VAR_COMMON_ARC,
                (sc_type.CONST_NODE, "_param"),
                sc_type.VAR_PERM_POS_ARC,
                relation
            )
            templ.triple(
                struct,
                sc_type.VAR_PERM_POS_ARC,
                "_self_rating_level"
            )
            search_results = search_by_template(templ)
            if search_results:
                return search_results[0].get('_param')
            return ScAddr()


        templ = ScTemplate()
        templ.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE_SCTRUCTURE, "_self_rating_struct"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_self_rating_and_system_rating_comparison", sc_type.CONST_NODE_NON_ROLE)
        )

        search_results = search_by_template(templ)
        if not search_results:
            return ScAddr(), ScAddr(), ScAddr()
        
        self_rating_struct = search_results[0].get("_self_rating_struct")

        self_rating_level = get_self_rating_params(
            user,
            self_rating_struct,
            ScKeynodes.resolve('nrel_self_rating_level', sc_type.CONST_NODE_NON_ROLE)
        )

        underrated_themes = get_self_rating_params(
            user,
            self_rating_struct,
            ScKeynodes.resolve('nrel_underrated_themes', sc_type.CONST_NODE_NON_ROLE)
        )

        overrated_themes = get_self_rating_params(
            user,
            self_rating_struct,
            ScKeynodes.resolve('nrel_overrated_themes', sc_type.CONST_NODE_NON_ROLE)
        )

        return self_rating_level, underrated_themes, overrated_themes
    

    def get_themes(themes_set: ScAddr) -> List[ScAddr]:
        themes = []

        themeTempl = ScTemplate()
        themeTempl.triple(
            themes_set,
            sc_type.VAR_PERM_POS_ARC,
            (sc_type.VAR_NODE, "_theme")
        )
        themeTempl.quintuple(
            "_theme",
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE_LINK, "_link"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_name", sc_type.CONST_NODE_NON_ROLE)
        )

        search_results = search_by_template(themeTempl)  
        for search_result in search_results:
            themes.append(str(get_link_content(search_result.get("_theme"))[0]))

    
        return themes
    

    def get_self_rating_discription(self_rating_level: ScAddr) -> str:
        templ = ScTemplate()
        templ.quintuple(
            self_rating_level,
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE_LINK, "_link"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_discription", sc_type.CONST_NODE_NON_ROLE)
        )

        search_results = search_by_template(templ)
        if search_results:
            return str(get_link_content(search_results[0].get("_link"))[0])
        return ''
    

    def get_studied_themes_set(user: ScAddr) -> ScAddr:
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
