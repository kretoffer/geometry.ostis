from sc_kpm import ScModule
from .compare_rating_of_progress_agent import CompareRatingOfProgressAgent
from .show_progress_agent import ShowProgressAgent
from .complicate_difficulty_agent import ComplicateDifficultyAgent
from .simplify_difficulty_agent import SimplifyDifficultyAgent

class ReflectionModule(ScModule):
    def __init__(self):
        super().__init__(
            CompareRatingOfProgressAgent(),
            ShowProgressAgent(),
            SimplifyDifficultyAgent(),
            ComplicateDifficultyAgent()
        )
