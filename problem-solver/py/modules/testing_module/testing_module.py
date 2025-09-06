from sc_kpm import ScModule
from .testing_agent import GetNextQuestionAgent
from .finish_test_agent import FinishTestAgent
from .answer_agent import AnswerAgent


class TestingModule(ScModule):
    def __init__(self):
        super().__init__(
            GetNextQuestionAgent(),
            AnswerAgent(),
            FinishTestAgent()
        )
