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


class FormTaskFromOlimpiadRecommendationsAgent(ScAgentClassic):
    def __init__(self):
        super().__init__("action_form_task_from_olimpiad_recommendations")
    
    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("FormTaskFromOlimpiadRecommendationsAgent finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result


    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("FormTaskFromOlimpiadRecommendationsAgent started")

        user, theme = get_action_arguments(action_node, 2)

        all_tests = self.get_all_tasks_from_olimpiads(theme)
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
        
    
        self.delete_previous_task_recommendations_for_user(user)
        self.set_recommendations_for_user(user, bad_problems, good_problems, other_problems)

        return ScResult.OK
    

    def get_all_tasks_from_olimpiads(theme: ScAddr) -> list[ScAddr]:
        templ = ScTemplate()
        templ.quintuple(
            (sc_type.VAR_NODE, "_task"),
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE, "_theme_set"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_themes", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.triple(
            "_theme_set",
            sc_type.VAR_PERM_POS_ARC,
            theme
        )
        templ.triple(
            ScKeynodes.resolve("concept_task_from_olimpiad", sc_type.CONST_NODE_CLASS),
            sc_type.VAR_PERM_POS_ARC,
            "_task"
        )
        templ.triple(
            ScKeynodes.resolve("concept_task", sc_type.CONST_NODE_CLASS),
            sc_type.VAR_PERM_POS_ARC,
            "_task"
        )
        search_results = search_by_template(templ)
        tasks = []
        if search_results:
            for result in search_results:
                tasks.append(result.get("_task"))
        return tasks
        

    

    def get_recommendations_for_this_task(user: ScAddr, task: ScAddr) -> float:
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
            return float(1.0 - get_link_content(search_results[0].get("_link")))
        return -100.0
    

    def delete_previous_task_recommendations_for_user(user: ScAddr) -> bool:
        templ = ScTemplate()
        templ.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            sc_type.VAR_NODE_STRUCTURE, "_recommendations_struct",
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_task_from_olimpiad_recommendations_for_user", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.quintuple(
            user,
            (sc_type.VAR_ACTUAL_TEMP_POS_ARC, "_prevous_arc"),
            (sc_type.VAR_NODE, "_previous_recommendations"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("rrel_task_recommendations", sc_type.CCONST_NODE_ROLE)
        )
        templ.triple(
            "_recommedation_struct",
            sc_type.VAR_PERM_POS_ARC,
            "_previous_recommendations"
        )

        search_results = search_by_template(templ)
        if search_results:
            previous_arc = search_results[0].get("_previous_arc")
            previous_recommendations_struct = search_results[0].get("_recommendations_struct")
            delete_elements(previous_arc, previous_recommendations_struct)
            return True
        return False


    def set_recommendations_for_user(user: ScAddr, bad_tasks: ScAddr, good_tasks: ScAddr, other_tasks: ScAddr) -> bool:
        templ = ScTemplate()
        templ.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            sc_type.VAR_NODE_STRUCTURE, "_recommendations_struct",
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_task_from_olimpiad_recommendations_for_user", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.quintuple(
            user,
            sc_type.VAR_ACTUAL_TEMP_POS_ARC,
            (sc_type.VAR_NODE, "_recommendations"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("rrel_task_recommendations", sc_type.CCONST_NODE_ROLE)
        )
        templ.triple(
            "_recommedation_struct",
            sc_type.VAR_PERM_POS_ARC,
            "_recommendations"
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
        return generating_results