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
        # находим первый элемент истории
        templ.quintuple(
            passing_test_history,
            (sc_type.VAR_PERM_POS_ARC, "_arc"),
            (sc_type.VAR_NODE, "question"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("rrel_1", sc_type.CONST_NODE_ROLE)
        )
        question = search_by_template(templ)[0].get("question")
        arc = search_by_template(templ)[0].get("_arc")
        # идём, пока не пройдём весь сет
        while True:
            templ = ScTemplate()
            templ.quintuple(
                arc,
                (sc_type.VAR_COMMON_ARC, "_connection_arc"),
                (sc_type.VAR_PERM_POS_ARC, "_second_arc"),
                sc_type.VAR_PERM_POS_ARC,
                ScKeynodes.resolve("nrel_basic_sequence", sc_type.CONST_NODE_NON_ROLE)
            )
            templ.triple(
                sc_type.VAR_NODE,
                "_second_arc",
                (sc_type.VAR_NODE, "_next_question")
            )
            search_results = search_by_template(templ)
            if not search_results:
                break
            question = search_by_template(templ)[0].get("_next_question")
            arc = search_by_template(templ)[0].get("_second_arc")
        templ = ScTemplate()
        # находим оттуда сам вопрос теста
        templ.quintuple(
            question,
            sc_type.VAR_PERM_POS_ARC,
            (sc_type.VAR_NODE, "_question"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("rrel_test_question", sc_type.CONST_NODE_ROLE)
        )
        search_results = search_by_template(templ)
        # не нашли -- завершаем с ошибкой
        if not search_results:
            return ScResult.ERROR

        question = search_results[0].get("_question")  

        arc = generate_connector(sc_type.CONST_PERM_POS_ARC, question, user_answer)
        generate_connector(sc_type.CONST_PERM_POS_ARC, ScKeynodes.resolve("rrel_question_answer", sc_type.CONST_NODE_ROLE), arc)

        create_action("action_get_next_question", user, test, question)
    
        self.logger.info("AnswerAgent: finished successfully")
        return ScResult.OK