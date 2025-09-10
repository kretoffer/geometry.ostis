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

from additions import get_difficulty_of_questiions, update_difficulty



logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s", datefmt="[%d-%b-%y %H:%M:%S]"
)


class ComplicateDifficultyWithTestAgent(ScAgentClassic):
    def __init__(self):
        super().__init__("action_complicate_difficulty")

    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("ComplicateDifficultyWithTestAgent finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result
    

    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("ComplicateDifficultyWithTestAgent started")

        user = get_action_arguments(action_node, 1)

        this_difficulty = get_difficulty_of_questiions(user)
        solved_level_up_test = self.get_solved_level_up_test(user, this_difficulty)

        if solved_level_up_test.is_valid():
            if self.is_enough(solved_level_up_test):
                # TODO триггер агента ComplicateDifficultyAgent
                pass
            else:
                self.erase_results_of_test(user, solved_level_up_test)
        else:
            # TODO триггер агента по выдаче заданий теста для повышения уровня
            pass


        return ScResult.OK



    def get_solved_level_up_test(user: ScAddr, this_difficulty: ScAddr) -> ScAddr:
        templ = ScTemplate()
        templ.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE, "_tests_set"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_solved_level_up_tests", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.triple(
            "_tests_set",
            sc_type.VAR_PERM_POS_ARC,
            (sc_type.VAR_NODE, "_test")
        )
        templ.qiuntuple(
            this_difficulty,
            sc_type.VAR_PERM_POS_ARC,
            "_test",
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("rrel_for_what_difficulty", sc_type.CONST_NODE_ROLE)
        )

        search_results = search_by_template(templ)
        if search_results:
            return search_results[0].get("_test")
        return ScAddr()
    

    def erase_results_of_test(user: ScAddr, test: ScAddr) -> bool:
        templ = ScTemplate()
        templ.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE, "_tests_set"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_solved_level_up_tests", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.triple(
            "_tests_set",
            (sc_type.VAR_PERM_POS_ARC, "_test_arc")
            (sc_type.VAR_NODE, "_test")
        )

        search_results = search_by_template(templ)
        if search_results:
            test_arc = search_results[0].get("_test_arc")
            delete_elements(test_arc)
            return True
        return False
    

    # TODO
    def is_enough(test: ScAddr) -> bool:
        pass
