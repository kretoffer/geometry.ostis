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
    get_link_content_data
)
from sc_kpm.utils.action_utils import (
    finish_action_with_status,
    get_action_arguments,
    generate_action_result
)
from sc_kpm import ScKeynodes



logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s", datefmt="[%d-%b-%y %H:%M:%S]"
)


class FormTaskRecommendationsForUserAgent(ScAgentClassic):
    def __init__(self):
        super().__init__("action_form_task_recommendations_for_user")
    
    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("FormTaskRecommendationsForUserAgent finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result


    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("FormTaskRecommendationsForUserAgent started")

        [user, theme] = get_action_arguments(action_node, 2)

        all_tests = self.get_all_tasks_on_this_theme(theme)
        bad_problems = []
        good_problems = []
        other_problems = []

        for test in all_tests:
            confidence = self.get_recommendations_for_this_task(user, test)
            match confidence:
                case x if 0.0 <= x <= 40.0:
                    bad_problems.append(test)
                case x if 75.0 < x <= 100.0:
                    good_problems.append(test)
                case _:
                    other_problems.append(test)
        
    
        
        generated_struct = self.set_recommendations_for_user(bad_problems, good_problems, other_problems)
        if generated_struct.is_valid():
            self.logger.info("FormTaskRecommendationsForUserAgent: recommendations are generated")
            generate_action_result(action_node, generated_struct)


        return ScResult.OK




    def get_all_tasks_on_this_theme(self, theme: ScAddr) -> List[ScAddr]:
        templ = ScTemplate()
        templ.triple(
            (sc_type.VAR_NODE, "_theme_set_of_problems"),
            sc_type.VAR_PERM_POS_ARC,
            theme
        )
        templ.quintuple(
            (sc_type.CONST_NODE, "_problem"),
            sc_type.VAR_COMMON_ARC,
            "_theme_set_of_problem",
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_themes", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.triple(
            "_problem",
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("concept_task", sc_type.CONST_NODE_CLASS)
        )

        search_results = search_by_template(templ)
        tasks = []
        if search_results:
            for result in search_results:
                tasks.append(result.get("_problem"))
        return tasks
    



    def set_recommendations_for_user(self, bad_tasks: ScAddr, good_tasks: ScAddr, other_tasks: ScAddr) -> ScAddr:
        templ = ScTemplate()
        templ.triple(
            (sc_type.VAR_NODE_STRUCTURE, "_recommedation_struct"),
            sc_type.VAR_PERM_POS_ARC,
            (sc_type.VAR_NODE, "_recommendations")
        )
        templ.quintuple(
            "_recommendations",
            sc_type.VAR_COMMON_ARC,
            good_tasks,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_good_tasks", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.quintuple(
            "_recommendations",
            sc_type.VAR_COMMON_ARC,
            bad_tasks,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_bad_tasks", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.quintuple(
            "_recommendations",
            sc_type.VAR_COMMON_ARC,
            other_tasks,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_other_tasks", sc_type.CONST_NODE_NON_ROLE)
        )


        generating_results = generate_by_template(templ)
        if not generating_results:
            return ScAddr()
        
        generated_struct = generating_results.get("_recommendation_struct")
        return generated_struct

        


    def get_recommendations_for_this_task(self, user: ScAddr, task: ScAddr) -> float:
        templ = ScTemplate()
        templ.quintuple(
            (sc_type.VAR_NODE, "_task_difficulty_info"),
            sc_type.VAR_ACTUAL_TEMP_POS_ARC,
            task,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("rrel_task", sc_type.CONST_NODE_ROLE)
        )
        templ.quintuple(
            "_task_difficulty_info",
            sc_type.VAR_ACTUAL_TEMP_POS_ARC,
            (sc_type.VAR_NODE_LINK, "_link"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("rrel_expected_difficulty", sc_type.CONST_NODE_ROLE)
        )
        templ.quintuple(
            "_task_difficulty_info",
            sc_type.VAR_ACTUAL_TEMP_POS_ARC,
            user,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("rrel_student", sc_type.CONST_NODE_ROLE)
        )

        search_results = search_by_template(templ)
        if search_results:
            return float(1.0 - get_link_content_data(search_results[0].get("_link")))
        return -100.0
        