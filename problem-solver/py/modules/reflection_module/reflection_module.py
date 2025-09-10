from sc_kpm import ScModule
from .compare_rating_of_progress_agent import CompareRatingOfProgressAgent
from .show_knowledge_level_agent import ShowKnowledgeLevelAgent
from .show_progress_agent import ShowProgressAgent
from .complicate_difficulty_agent import ComplicateDifficultyAgent
from .complicate_difficulty_with_test_agent import ComplicateDifficultyWithTestAgent
from .simplify_difficulty_agent import SimplifyDifficultyAgent

class ReflectionModule(ScModule):
    def __init__(self):
        super().__init__(
            CompareRatingOfProgressAgent(),
            ShowKnowledgeLevelAgent(),
            ShowProgressAgent(),
            SimplifyDifficultyAgent(),
            ComplicateDifficultyAgent(),
            ComplicateDifficultyWithTestAgent()
        )
