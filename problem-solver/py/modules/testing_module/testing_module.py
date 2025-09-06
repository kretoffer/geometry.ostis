from sc_kpm import ScModule
from .testing_agent import GetNextQuestionAgent
from .finish_test_agent import FinishTestAgent


class TestingModule(ScModule):
    def __init__(self):
        super().__init__(
            GetNextQuestionAgent(),
            #FinishTestAgent()
        )
