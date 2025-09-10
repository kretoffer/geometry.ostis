from sc_kpm import ScModule
from .compare_rating_of_progress_agent import CompareRatingOfProgressAgent
from .show_knowledge_level_agent import ShowKnowledgeLevelAgent
from .show_progress_agent import ShowProgressAgent

class ReflectionModule(ScModule):
    def __init__(self):
        super().__init__(
            CompareRatingOfProgressAgent(),
            ShowKnowledgeLevelAgent(),
            ShowProgressAgent()
        )
