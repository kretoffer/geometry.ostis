from sc_kpm import ScModule
from .compare_rating_of_progress_agent import CompareRatingOfProgressAgent


class ReflectionModule(ScModule):
    def __init__(self):
        super().__init__(
            CompareRatingOfProgressAgent()
        )
