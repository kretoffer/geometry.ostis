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

from .additions import get_middle_tasks_solutions, get_all_stidied_themes


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s", datefmt="[%d-%b-%y %H:%M:%S]"
)


class FormThemeRecommendationsForUserToStudyAgent(ScAgentClassic):
    def __init__(self):
        super().__init__("action_form_theme_recommendations_for_user_to_study")
    
    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("FormThemeRecommendationsForUserToStudyAgent finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result


    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("FormThemeRecommendationsForUserToStudyAgent started")

        user = get_action_arguments(action_node, 1)

        all_stidied_themes = get_all_stidied_themes(user)

        all_low_stidied_themes = []
        all_stidied_themes_results = {}
        for theme in all_stidied_themes:
            middle_tasks_solutions = get_middle_tasks_solutions(user, theme)
            all_stidied_themes_results[theme] = middle_tasks_solutions
            if middle_tasks_solutions <= 0.5:
                all_stidied_themes.append(theme)


        good_themes = []
        bad_themes = []
        for theme in all_low_stidied_themes:
            if self.is_recommended_theme(theme, all_stidied_themes_results):
                good_themes.append(theme)
            else:
                bad_themes.append(theme)

        other_themes = [el for el in all_stidied_themes if el not in good_themes and el not in bad_themes]

        
        return ScResult.OK
    


    def is_recommended_theme(theme: ScAddr, themes_dict: dict) -> bool:
        def get_requirements_of_this_theme(theme: ScAddr) -> List[ScAddr]:
            templ = ScTemplate()
            templ.quintuple(
                (sc_type.VAR_NODE, "_theme_set"),
                sc_type.VAR_COMMON_ARC,
                theme,
                sc_type.VAR_PERM_POS_ARC,
                ScKeynodes.resolve("nrel_themes_before_this", sc_type.CONST_NODE_NON_ROLE)
            )
            templ.triple(
                "_theme_set",
                sc_type.VAR_PERM_POS_ARC,
                (sc_type.VAR_NODE, "_theme")
            )

            search_results = search_by_template(templ)
            themes = []
            if search_results:
                for result in search_results:
                    themes.append(result.get("_theme"))
            return themes
        
        themes_list = get_requirements_of_this_theme(theme)
        for themes_el in themes_list:
            if themes_el not in themes_dict or themes_dict[themes_el] <= 0.5:
                return False
        return True
