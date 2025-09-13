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


from .additions import get_middle_tasks_solutions, get_all_stidied_themes, get_all_not_stidied_themes
from .additions import create_sc_set


class FormThemeRecommendationsForUserToSolveTestOrProblemAgent(ScAgentClassic):
    def __init__(self):
        super().__init__("action_form_theme_recommendations_for_user_to_solve_test_or_problem")
    
    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("FormThemeRecommendationsForUserToSolveTestOrProblemAgent finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result


    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("FormThemeRecommendationsForUserToSolveTestOrProblemAgent started")

        user = get_action_arguments(action_node, 1)

        all_stidied_themes = get_all_stidied_themes(user)
        all_stidied_themes_results = {}
        for theme in all_stidied_themes:
            middle_tasks_solutions = get_middle_tasks_solutions(user, theme)
            all_stidied_themes_results[theme] = middle_tasks_solutions

        
        good_themes = []
        other_themes = []


        good_themes.extend(get_all_not_stidied_themes(user))

        for theme in all_stidied_themes_results:
            knowledge_level = all_stidied_themes_results[theme]
            if knowledge_level < 0.8 and knowledge_level > 0.4:
                good_themes.append(theme)
                continue
            other_themes.append(theme)

        good_themes_set = create_sc_set(good_themes)
        other_themes_set = create_sc_set(other_themes)

        recommendations_struct, recommendations_set = self.get_theme_recommendations_for_solve_test_or_problem(user)
        self.set_theme_recommendations_for_solve_test_or_problem(user, [recommendations_struct, recommendations_set], good_themes, other_themes)
        
        return ScResult.OK
    


    def get_theme_recommendations_for_solve_test_or_problem(user: ScAddr) -> tuple[ScAddr, ScAddr]:
        templ = ScTemplate()
        templ.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE_STRUCTURE, "_recommendations_struct"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_user_theme_recommendations_to_solve_test_or_problem", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE, "_recommendations"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_user_theme_recommendations", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.triple(
            "_recommendations_struct",
            sc_type.VAR_PERM_POS_ARC,
            "_recommendations"
        )
        
        search_results = search_by_template(templ)
        if search_results:
            return search_results[0].get("_recommendations_struct"), search_results[0].get("_recommendations")
        return ScAddr(), ScAddr()
    

    

    def set_theme_recommendations_for_solve_test_or_problem(user: ScAddr, recommendations: list[ScAddr], good_themes: ScAddr, other_themes: ScAddr) -> bool:
        def delete_theme_recommendations_option_for_solve_test_or_problem(recommendations: list[ScAddr], relation: ScAddr) -> bool:
            recommendations_struct = recommendations[0]
            recommendations_set = recommendations[1]
            templ = ScTemplate()
            templ.quintuple(
                recommendations_set,
                (sc_type.VAR_PERM_POS_ARC, "_previous_arc"), 
                (sc_type.VAR_NODE, "_previous_theme_set"),
                sc_type.VAR_PERM_POS_ARC,
                relation
            )
            templ.triple(
                recommendations_struct,
                sc_type.VAR_PERM_POS_ARC,
                "_previous_theme_set"
            )

            search_results = search_by_template(templ)
            if not search_results:
                return True
            
            previous_arc = search_results[0].get("_previous_arc")
            previous_themes = search_results[0].get("_previous_theme_set")
            return delete_elements(previous_arc, previous_themes)
        

        good_themes_set = create_sc_set(good_themes)
        other_themes_set = create_sc_set(other_themes)


        delete_theme_recommendations_option_for_solve_test_or_problem(
            recommendations,
            ScKeynodes.resolve("rrel_good_themes", sc_type.CONST_NODE_ROLE)
        )
        delete_theme_recommendations_option_for_solve_test_or_problem(
            recommendations,
            ScKeynodes.resolve("rrel_other_themes", sc_type.CONST_NODE_ROLE)
        )

        recommendations_struct = recommendations[0]
        recommendations_set = recommendations[1]
        templ = ScTemplate()
        templ.triple(
            recommendations_struct,
            sc_type.VAR_PERM_POS_ARC,
            recommendations_set
        )
        templ.quintuple(
            recommendations_set,
            sc_type.VAR_PERM_POS_ARC,
            good_themes_set,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("rrel_good_themes", sc_type.CONST_NODE_ROLE)
        )
        templ.quintuple(
            recommendations_set,
            sc_type.VAR_PERM_POS_ARC,
            other_themes_set,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("rrel_other_themes", sc_type.CONST_NODE_ROLE)
        )

        return generate_by_template(templ)
