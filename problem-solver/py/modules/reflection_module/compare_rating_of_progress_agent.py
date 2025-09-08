import logging
from typing import List
from sc_client.models import ScAddr, ScTemplate
from sc_client.constants import sc_type
from sc_client.client import search_by_template, generate_by_template, delete_elements

from sc_kpm import ScAgentClassic, ScResult
from sc_kpm.sc_sets import ScSet
from sc_kpm.utils import (
    generate_connector,
    generate_node
)
from sc_kpm.utils.action_utils import (
    finish_action_with_status,
    get_action_arguments
)
from sc_kpm import ScKeynodes



logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s", datefmt="[%d-%b-%y %H:%M:%S]"
)


class CompareRatingOfProgressAgent(ScAgentClassic):
    def __init__(self):
        super().__init__("action_compare_rating_of_progress")
    
    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("CompareRatingOfProgressAgent finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result


    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("CompareRatingOfProgressAgent started")

        user = get_action_arguments(action_node, 1)

        system_rating = self.get_rating(
            user,
            ScKeynodes.resolve("nrel_system_rating", sc_type.CONST_NODE_NON_ROLE)
        )
        user_rating = self.get_rating(
            user,
            ScKeynodes.resolve("nrel_self_rating", sc_type.CONST_NODE_NON_ROLE)
        )

        system_worth_studied_themes = self.get_themes(
            system_rating,
            user, 
            ScKeynodes.resolve("nrel_worth_studied_themes", sc_type.CONST_NODE_NON_ROLE))
        system_well_studied_themes = self.get_themes(
            system_rating,
            user, 
            ScKeynodes.resolve("nrel_well_studied_themes", sc_type.CONST_NODE_NON_ROLE))


        user_self_rated_worth_studied_themes = self.get_themes(
            user_rating,
            user, 
            ScKeynodes.resolve("nrel_worth_studied_themes", sc_type.CONST_NODE_NON_ROLE))
        user_self_rated_well_studied_themes = self.get_themes(
            user_rating,
            user, 
            ScKeynodes.resolve("nrel_well_studied_themes", sc_type.CONST_NODE_NON_ROLE))
        
        underrated_themes_lists = self.define_misjudged_themes(
            user_themes = user_self_rated_worth_studied_themes,
            system_themes = system_well_studied_themes
        )

        overrated_themes_lists = self.define_misjudged_themes(
            user_themes = user_self_rated_well_studied_themes,
            system_themes = system_worth_studied_themes
        )

        user_self_rating = self.get_rating(
            user,
            ScKeynodes.resolve("nrel_self_rating_and_system_rating_comparison", sc_type.CONST_NODE_NON_ROLE)
        )

        overrated_themes_set = self.create_sc_set(overrated_themes_lists)
        underrated_themes_set = self.create_sc_set(underrated_themes_lists)

        self.update_underrated_themes(user_self_rating, underrated_themes_set)
        self.update_overrated_themes(user_self_rating, overrated_themes_set)

        return ScResult.OK


    def get_rating(user: ScAddr, relation: ScAddr) -> ScAddr:
        templ = ScTemplate()
        templ.quintuple(
            user,
            sc_type.COMMON_ARC,
            (sc_type.VAR_NODE_STRUCTURE, "_rating"),
            sc_type.VAR_PERM_POS_ARC,
            relation
        )

        search_results = search_by_template()
        if search_results:
            return search_results[0].get("_rating")
        return ScAddr()


    def get_themes(system_rating: ScAddr, user: ScAddr, relation: ScAddr) -> List[ScAddr]:
        themes = []

        templ = ScTemplate()
        templ.triple(
            system_rating,
            sc_type.VAR_PERM_POS_ARC,
            (sc_type.VAR_NODE, "_themes_set")
        )
        templ.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            "_themes_set",
            sc_type.VAR_PERM_POS_ARC,
            relation
        )

        search_results = search_by_template()
        if search_results:
            themes_set = search_results[0].get("_themes_set")
            themeTempl = ScTemplate()
            themeTempl.triple(
                themes_set,
                sc_type.VAR_PERM_POS_ARC,
                (sc_type.VAR_NODE, "_theme")
            )

            search_results = search_by_template()  
            for search_result in search_results:
                themes.append(search_result.get("_theme"))
        
        return themes

    def update_underrated_themes(self_rating: ScAddr, new_themes: ScAddr) -> bool:
        templ_for_searching = ScTemplate()
        templ_for_searching.quintuple(
            self_rating,
            (sc_type.VAR_COMMON_ARC, "_previous_arc")
            (sc_type.VAR_NODE, "_previous_set"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_underrated_themes", sc_type.CONST_NODE_NON_ROLE)
        )

        search_results = search_by_template(templ_for_searching)

        if not search_results:
            return False
        previous_set = search_results[0].get("_previous_set")
        previous_arc = search_results[0].get("_previous_arc")

        delete_elements(previous_set, previous_arc)

        templ_for_generating = ScTemplate()
        templ_for_generating.quintuple(
            self_rating,
            sc_type.VAR_COMMON_ARC,
            new_themes,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_underated_themes", sc_type.CONST_NODE_NON_ROLE)
        )

        generate_results = generate_by_template(templ_for_generating)
        return generate_results


    def update_overrated_themes(self_rating: ScAddr, new_themes: ScAddr) -> bool:
        templ_for_searching = ScTemplate()
        templ_for_searching.quintuple(
            self_rating,
            (sc_type.VAR_COMMON_ARC, "_previous_arc")
            (sc_type.VAR_NODE, "_previous_set"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_overrated_themes", sc_type.CONST_NODE_NON_ROLE)
        )

        search_results = search_by_template(templ_for_searching)

        if not search_results:
            return False
        

        previous_set = search_results[0].get("_previous_set")
        previous_arc = search_results[0].get("_previous_arc")

        delete_elements(previous_set, previous_arc)

        templ_for_generating = ScTemplate()
        templ_for_generating.quintuple(
            self_rating,
            sc_type.VAR_COMMON_ARC,
            new_themes,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_overrated_themes", sc_type.CONST_NODE_NON_ROLE)
        )

        generate_results = generate_by_template(templ_for_generating)
        return generate_results


    def create_sc_set(self, themes: list[ScAddr]) -> ScAddr:
        sc_set = ScSet()
        for theme in themes:
            sc_set.add(theme)
        return sc_set


    def define_misjudged_themes(user_themes: ScAddr, system_themes: ScAddr) -> list[ScAddr]:
        user_set = set(user_themes)
        system_set = set(system_themes) 
        return list(user_set & system_set)






