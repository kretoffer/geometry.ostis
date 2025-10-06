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

from .additions import create_sc_set



logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s", datefmt="[%d-%b-%y %H:%M:%S]"
)


class FormTestRecommendationsForUserAgent(ScAgentClassic):
    def __init__(self):
        super().__init__("action_form_test_recommendations_for_user")
    
    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("FormTestRecommendationsForUserAgent finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result


    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("FormTestRecommendationsForUserAgent started")

        [user, theme] = get_action_arguments(action_node, 2)

        all_tests = self.get_all_test_on_this_theme(theme)
        bad_tests = []
        good_tests = []
        other_tests = []

        for test in all_tests:
            confidence = self.get_recommendations_for_this_test(user, test)
            match confidence:
                case x if 0.0 <= x <= 40.0:
                    bad_tests.append(test)
                case x if 75.0 < x <= 100.0:
                    good_tests.append(test)
                case _:
                    other_tests.append(test)
        
    
        generated_struct = self.set_recommendations_for_user(
            create_sc_set(bad_tests), 
            create_sc_set(good_tests), 
            create_sc_set(other_tests)
        )
        if generated_struct.is_valid():
            self.logger.info("FormTestRecommendationsForUserAgent: recommendations are generated")
            generate_action_result(action_node, generated_struct)

        return ScResult.OK




    def get_all_test_on_this_theme(self, theme: ScAddr) -> List[ScAddr]:
        templ = ScTemplate()
        templ.triple(
            (sc_type.VAR_NODE, "_theme_set_of_test"),
            sc_type.VAR_PERM_POS_ARC,
            theme
        )
        templ.quintuple(
            (sc_type.VAR_NODE, "_test"),
            sc_type.VAR_COMMON_ARC,
            "_theme_set_of_test",
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_themes", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.triple(
            "_test",
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("concept_test", sc_type.CONST_NODE_CLASS)
        )

        search_results = search_by_template(templ)
        tests = []
        if search_results:
            for result in search_results:
                tests.append(result.get("_test"))
        return tests
    

    def set_recommendations_for_user(self, bad_tests: ScAddr, good_tests: ScAddr, other_tests: ScAddr) -> bool:
        templ = ScTemplate()
        templ.triple(
            (sc_type.VAR_NODE_STRUCTURE, "_recommedation_struct"),
            sc_type.VAR_PERM_POS_ARC,
            (sc_type.VAR_NODE, "_recommendations")
        )
        templ.quintuple(
            "_recommendations",
            sc_type.VAR_COMMON_ARC,
            good_tests,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_good_tests", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.quintuple(
            "_recommendations",
            sc_type.VAR_COMMON_ARC,
            bad_tests,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_bad_tests", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.quintuple(
            "_recommendations",
            sc_type.VAR_COMMON_ARC,
            other_tests,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_other_tests", sc_type.CONST_NODE_NON_ROLE)
        )


        generating_results = generate_by_template(templ)
        if not generating_results:
            return ScAddr()
        
        generated_struct = generating_results.get("_recommedation_struct")
        return generated_struct


        


    def get_recommendations_for_this_test(self, user: ScAddr, test: ScAddr) -> float:
        templ = ScTemplate()
        templ.quintuple(
            (sc_type.VAR_NODE, "_test_difficulty_info"),
            sc_type.VAR_ACTUAL_TEMP_POS_ARC,
            test,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("rrel_test", sc_type.CONST_NODE_ROLE)
        )
        templ.quintuple(
            "_test_difficulty_info",
            sc_type.VAR_ACTUAL_TEMP_POS_ARC,
            (sc_type.VAR_NODE_LINK, "_link"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("rrel_expected_difficulty", sc_type.CONST_NODE_ROLE)
        )
        templ.quintuple(
            "_test_difficulty_info",
            sc_type.VAR_ACTUAL_TEMP_POS_ARC,
            user,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("rrel_student", sc_type.CONST_NODE_ROLE)
        )

        search_results = search_by_template(templ)
        if search_results:
            return float(1.0 - get_link_content_data(search_results[0].get("_link")))
        return -100.0
        