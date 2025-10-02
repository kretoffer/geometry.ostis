import logging
from sc_client.models import ScAddr, ScTemplate, ScConstruction
from sc_client.constants import sc_type
from sc_client.client import search_by_template, generate_elements
from sc_client.client import delete_elements

from sc_kpm import ScAgentClassic, ScResult
from sc_kpm.utils.action_utils import (
    finish_action_with_status,
    get_action_arguments
)
from sc_kpm import ScKeynodes

from random import choice


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s", datefmt="[%d-%b-%y %H:%M:%S]"
)

class StartTestAgent(ScAgentClassic):
    def __init__(self):
        super().__init__("action_start_test")

    
    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("StartTestAgent finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result
    

    def run(self, action: ScAddr) -> ScResult:
        self.logger.info("StartTestAgent started")

        # rrel_1 -> (action -> user);;
        # rrel_2 -> (action -> test);;
        [user, test] = get_action_arguments(action, 2)

        self.remove_current_test(user)
        
        templ = ScTemplate()
        templ.quintuple(
            test,
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE_TUPLE, "questions_set"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_decomposition", sc_type.VAR_NODE_NON_ROLE)
        )
        templ.quintuple(
            "questions_set",
            sc_type.VAR_PERM_POS_ARC,
            (sc_type.VAR_NODE, "first_question"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.rrel_index(1)
        )
        first_question = search_by_template(templ)[0].get("first_question")

        constr = ScConstruction()

        constr.generate_connector(sc_type.CONST_COMMON_ARC, user, test, "arc_to_test")
        constr.generate_connector(sc_type.CONST_PERM_POS_ARC, ScKeynodes.resolve("nrel_current_test", sc_type.VAR_NODE_NON_ROLE), "arc_to_test")

        constr.generate_node(sc_type.CONST_NODE, "passing_test_history")
        constr.generate_connector(sc_type.CONST_COMMON_ARC, "arc_to_test", "passing_test_history", "arc_to_passing_test_history")

        constr.generate_connector(sc_type.CONST_PERM_POS_ARC, ScKeynodes.resolve("nrel_user_passing_test_history", sc_type.VAR_NODE_NON_ROLE), "arc_to_passing_test_history")

        constr.generate_node(sc_type.CONST_NODE, "question")
        constr.generate_connector(sc_type.CONST_PERM_POS_ARC, "question", first_question, "arc_to_first_question")
        constr.generate_connector(sc_type.CONST_PERM_POS_ARC, ScKeynodes.resolve("rrel_test_question", sc_type.VAR_NODE_ROLE), "arc_to_first_question")
        constr.generate_connector(sc_type.CONST_PERM_POS_ARC, "passing_test_history", "question", "arc_from_pth2q")
        constr.generate_connector(sc_type.CONST_PERM_POS_ARC, ScKeynodes.rrel_index(1), "arc_from_pth2q")
        constr.generate_connector(sc_type.CONST_PERM_POS_ARC, ScKeynodes.resolve("rrel_last", sc_type.VAR_NODE_ROLE), "arc_from_pth2q")

        constr.generate_connector(sc_type.CONST_PERM_POS_ARC, "question", user, "arc_to_user")
        constr.generate_connector(sc_type.CONST_PERM_POS_ARC, ScKeynodes.resolve("rrel_passer", sc_type.VAR_NODE_ROLE), "arc_to_user")

        generate_elements(constr)


        self.logger.info("StartTestAgent: finished successfully")
        return ScResult.OK
    
    def remove_current_test(self, user: ScAddr):
        templ = ScTemplate()
        templ.quintuple(
            user,
            (sc_type.VAR_COMMON_ARC, "arc_to_test"),
            sc_type.VAR_NODE,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_current_test", sc_type.VAR_NODE_NON_ROLE)
        )
        search_results = search_by_template(templ)
        for search_result in search_results:
            delete_elements(search_result.get("arc_to_test"))
