import logging
from sc_client.models import ScAddr, ScTemplate
from sc_client.constants import sc_type
from sc_client.client import search_by_template, generate_by_template, delete_elements

from sc_kpm import ScAgentClassic, ScResult
from sc_kpm.utils import (
    generate_connector,
    generate_node
)
from sc_kpm.utils.action_utils import (
    finish_action_with_status,
    get_action_arguments
)
from sc_kpm import ScKeynodes

from .additions import get_user_passing_test_history, is_question_answer_correct
from utils.create_action import create_action



logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s", datefmt="[%d-%b-%y %H:%M:%S]"
)


# function GetNextTestQuestionAfterUserAnsweredQuestion(user: User, test: Test, question: Question) -> Question:
#     nextQuestion: Question = None
#     passingTestHistory: PassingTestHistory = None

#     // Ecли вопрос указан (то есть пользователь ответил на него),
#     if IsValid(question):
#         // то тогда ищем в зависимости от ответа на этот вопрос и параметров этого вопроса следующий вопрос
#         passingTestHistory = GetUserPassingTestHistory(user, test)
#         questionAnswer: QuestionAnswer = GetUserQuestionAnswer(passingTestHistory, question)
        
#         // Если ответ на вопрос правильный,
#         if IsQuestionAnswerCorrect(questionAnswer, question):
#             // то тогда ищем следующий вопрос с учётом того, что ответ на текущий вопрос был дан правильно
#             nextQuestion = GetNextTestQuestionIfUserAnsweredQuestionCorrectly(passingTestHistory, question, questionAnswer)
#         else
#             // иначе - с учётом того, что ответ на текущий вопрос был дан не правильно
#             nextQuestion = GetNextTestQuestionIfUserAnsweredQuestionNotCorrectly(passingTestHistory, question, questionAnswer)
#     else:
#         // иначе инициализируем историю прохождения теста пользователем и ищем первый вопрос в тесте
#         passingTestHistory = InitializeUserPassingTestHistory(user, test)
#         nextQuestion = GetFirstTestQuestion(passingTestHistory)

#     return nextQuestion
# end
class GetNextQuestionAgent(ScAgentClassic):
    def __init__(self):
        super().__init__("action_get_next_question")

    
    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("GetNextQuestionAgent finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result
    

    def run(self, action: ScAddr) -> ScResult:
        self.logger.info("GetNextQuestionAgent started")

        # rrel_1 -> (action -> user);;
        # rrel_2 -> (action -> test);;
        # rrel_3 -> (action -> question);;
        [user, test, question] = get_action_arguments(action, 3)

        if question.is_valid():
            passing_test_history = get_user_passing_test_history(user, test)
            question_answer = self.get_user_question_answer(question)

        templ = ScTemplate()
        templ.quintuple(
            question,
            sc_type.VAR_PERM_POS_ARC,
            (sc_type.VAR_NODE, "_question"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("rrel_test_question", sc_type.CONST_NODE_ROLE)
        )
        question_ref = search_by_template(templ)[0].get("_question")
        
        next_question: ScAddr = self.get_next_question(user, test, question_ref, is_question_answer_correct(question_answer, question_ref), passing_test_history)


        templ = ScTemplate()
        templ.quintuple(
            passing_test_history,
            (sc_type.VAR_PERM_POS_ARC, "_last_arc"),
            question,
            (sc_type.VAR_PERM_POS_ARC, "_arc_to_last_arc"),
            ScKeynodes.resolve("rrel_last", sc_type.CONST_NODE_ROLE)
        )
        search_results = search_by_template(templ)
        if search_results:
            search_result = search_results[0]
            delete_elements(search_result.get("_arc_to_last_arc"))

            if next_question.is_valid(): 
                question_arc: ScAddr = generate_connector(sc_type.CONST_PERM_POS_ARC, passing_test_history, next_question)
                arc = generate_connector(sc_type.CONST_COMMON_ARC, search_result.get("_last_arc"), question_arc)
                generate_connector(sc_type.CONST_PERM_POS_ARC, ScKeynodes.resolve("nrel_basic_sequence", sc_type.CONST_NODE_NON_ROLE), arc)
                generate_connector(sc_type.CONST_PERM_POS_ARC, ScKeynodes.resolve("rrel_last", sc_type.CONST_NODE_ROLE), question_arc)
            else:
                create_action("action_finish_test", user, test)

        else:
            return ScResult.ERROR

    
        self.logger.info("GetNextQuestionAgent: finished successfully")
        return ScResult.OK
    
    #
    #   
    #         nrel_current_test
    #                |
    #                |
    # //            \/
    # // misha ===========> test_1
    # //            ||
    # //            ||
    # //            || <------- nrel_user_passing_test_history
    # //            ||
    # //            \/
    # //      misha_passing_test_1_history-------------------
    # //            |                                        |
    # //            |                                        |
    # // rrel_1 --> |=======================================>| <--- rrel_last
    # //            |        /\                              |
    # //            \/       |---------- nrel_basic_sequence \/
    # //        -----O-----------------------------------    O     
    # //        |                  |                    |
    # //        |                  |                    |
    # // rrel_test_question rrel_question_answer rrel_passer
    # //        |                  |                    |
    # //        |                  |                    |
    # //       \/                  \/                   \/
    # // test_1_question_1  test_1_question_1_answer_1 misha
    # //

    # @misha_passing_test_1_history = <
    #     {
    #         rrel_test_question: test_1_question_1;
    #         rrel_question_answer: test_1_question_1_answer_1;
    #         rrel_passer: misha
    #     };
    #     {
    #         rrel_test_question: test_1_question_2;
    #         rrel_question_answer: test_1_question_2_answer_3;
    #         rrel_passer: misha
    #     }
    # >;;

    def get_user_question_answer(self, question: ScAddr) -> ScAddr:
         # passing_test_history -> {rrel_test_question: question, rrel_question_answer: answer, rrel_passer: user};;
        templ = ScTemplate()
        templ.quintuple(
            question,
            sc_type.VAR_PERM_POS_ARC,
            (sc_type.VAR_NODE, "_question_answer"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("rrel_question_answer", sc_type.CONST_NODE_ROLE)
        )
        search_results = search_by_template(templ)

        if search_results:
            search_result = search_results[0]
            return search_result.get("_question_answer")
        
        return ScAddr()


    def initialize_user_passing_test_history(self, user: ScAddr, test: ScAddr) -> ScAddr:
        # nrel_user_passing_test_history -> ((user => test) => user_passing_test_history);;
        templ = ScTemplate()
        # nrel_user_passing_test_history -> ((=>) => user_passing_test_history)
        templ.quintuple(
            (sc_type.VAR_COMMON_ARC, "_common_arc"),                #        =>
            sc_type.VAR_COMMON_ARC,                                 #        || 
                                                                    #        \/
            (sc_type.VAR_NODE, "_user_passing_test_history"),       # user_passing_test_history
            sc_type.VAR_PERM_POS_ARC,                               #                <-
            ScKeynodes.resolve("nrel_user_passing_test_history", sc_type.CONST_NODE_NON_ROLE)
        )
        # (user => test)
        templ.triple(
            user,
            "_common_arc", # => 
            test
        )

        generate_results = generate_by_template(templ)
        return generate_results.get("_user_passing_test_history")
        

    def get_harder_question(self, questions_set: ScAddr, question: ScAddr) -> ScAddr:
        templ = ScTemplate()
        templ.triple(
            questions_set,
            (sc_type.VAR_PERM_POS_ARC, "_last_question_arc"),
            question
        )
        search_results = search_by_template(templ)
        if not search_results:
            return ScAddr()
        last_question_arc = search_results[0].get("_last_question_arc")

        templ = ScTemplate()

        # ищем следующую дугу и вопрос
        templ.quintuple(
            last_question_arc,
            (sc_type.VAR_COMMON_ARC, "_connection_arc"),
            (sc_type.VAR_PERM_POS_ARC, "_second_arc"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_basic_sequence", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.triple(
            questions_set,
            "_second_arc",
            (sc_type.VAR_NODE, "_next_question")
        )

        search_results = search_by_template(templ)
        # если не нашли ничего -- прошли весь сет. возвращаем пустой адрес
        if not search_results:
            return ScAddr()
        
        more_hard_question = search_results[0].get("_next_question")
        return more_hard_question
    

    def get_simplier_question(self, questions_set: ScAddr, question: ScAddr) -> ScAddr:
        templ = ScTemplate()
        templ.triple(
            questions_set,
            (sc_type.VAR_PERM_POS_ARC, "_last_question_arc"),
            question
        )
        search_results = search_by_template(templ)
        if not search_results:
            return ScAddr()
        last_question_arc = search_results[0].get("_last_question_arc")

        templ = ScTemplate()

        # ищем следующую дугу и вопрос, но теперь идём "назад"
        templ.quintuple(
            (sc_type.VAR_PERM_POS_ARC, "_second_arc"),
            (sc_type.VAR_COMMON_ARC, "_connection_arc"),
            last_question_arc,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_basic_sequence", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.triple(
            questions_set,
            "_second_arc",
            (sc_type.VAR_NODE, "_next_question")
        )

        search_results = search_by_template(templ)
        if not search_results:
            return ScAddr()
        
        more_simple_question = search_results[0].get("_next_question")
        return more_simple_question


    def get_next_question(self, user: ScAddr, test: ScAddr, question: ScAddr, question_is_correct: bool, passing_test_hitory) -> ScAddr:
        templ = ScTemplate()
        templ.quintuple(
            test,
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE_TUPLE, "_set"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_decomposition", sc_type.VAR_NODE_NON_ROLE)
        )
        questions_set = search_by_template(templ)[0].get("_set")

        correct_question = None
        while correct_question is None:
            if question_is_correct:
                next_question = self.get_harder_question(questions_set, question)
            else: 
                next_question = self.get_simplier_question(questions_set, question)
            
            if not next_question.is_valid():
                return ScAddr()
            question = next_question
            
            templ = ScTemplate()
            templ.triple(
                passing_test_hitory,
                sc_type.VAR_PERM_POS_ARC,
                (sc_type.VAR_NODE, "element")
            )
            templ.quintuple(
                "element",
                sc_type.VAR_PERM_POS_ARC,
                next_question,
                sc_type.VAR_PERM_POS_ARC,
                ScKeynodes.resolve("rrel_test_question", sc_type.VAR_NODE_ROLE)
            )

            if not search_by_template(templ):
                correct_question = next_question
        
        new_question = generate_node(sc_type.CONST_NODE)
        user_connector = generate_connector(sc_type.CONST_PERM_POS_ARC, new_question, user)
        generate_connector(sc_type.CONST_PERM_POS_ARC, ScKeynodes.resolve("rrel_passer", sc_type.CONST_NODE_ROLE), user_connector)

        arc = generate_connector(sc_type.CONST_PERM_POS_ARC, new_question, correct_question)
        generate_connector(sc_type.CONST_PERM_POS_ARC, ScKeynodes.resolve("rrel_test_question", sc_type.CONST_NODE_ROLE), arc)

        return new_question
