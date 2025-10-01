import logging
from sc_client.models import ScAddr, ScTemplate
from sc_client.constants import sc_type
from sc_client.client import search_by_template

from sc_kpm import ScAgentClassic, ScResult
from sc_kpm.utils import (
    generate_connector
)
from sc_kpm.utils.action_utils import (
    finish_action_with_status,
    get_action_arguments
)
from sc_kpm import ScKeynodes

from .additions import get_user_passing_test_history
from utils.create_action import create_action


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s", datefmt="[%d-%b-%y %H:%M:%S]"
)

class AnswerAgent(ScAgentClassic):
    def __init__(self):
        super().__init__("action_answered_test_question")

    
    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("AnswerAgent finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result
    

    def run(self, action: ScAddr) -> ScResult:
        self.logger.info("AnswerAgent started")

        # rrel_1 -> (action -> user);;
        # rrel_2 -> (action -> test);;
        # rrel_3 -> (action -> answer);;
        [user, test, user_answer] = get_action_arguments(action, 3)
        passing_test_history = get_user_passing_test_history(user, test)

        templ = ScTemplate()
        templ.quintuple(
            passing_test_history,
            sc_type.VAR_PERM_POS_ARC,
            (sc_type.NODE, "_last_question"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("rrel_last", sc_type.CONST_NODE_ROLE)
        )
        search_results = search_by_template(templ)
        if search_results:
            search_result = search_results[0]
            arc = generate_connector(sc_type.CONST_PERM_POS_ARC, search_result.get("_last_question"), user_answer)
            generate_connector(sc_type.CONST_PERM_POS_ARC, ScKeynodes.resolve("rrel_question_answer", sc_type.CONST_NODE_ROLE), arc)

            create_action("action_get_next_question", user, test, search_result.get("_last_question"))
    
        self.logger.info("AnswerAgent: finished successfully")
        return ScResult.OK