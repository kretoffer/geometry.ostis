from sc_kpm import ScModule
from .get_next_question_agent import GetNextQuestionAgent
from .finish_test_agent import FinishTestAgent
from .answer_agent import AnswerAgent
from .start_test_agent import StartTestAgent


class TestingModule(ScModule):
    def __init__(self):
        super().__init__(
            GetNextQuestionAgent(),
            AnswerAgent(),
            FinishTestAgent(),
            StartTestAgent()
        )
