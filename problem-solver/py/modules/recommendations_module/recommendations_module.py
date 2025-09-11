from sc_kpm import ScModule
from .form_test_recommendations_for_user_agent import FormTestRecommendationsForUserAgent


class RecommendationsModule(ScModule):
    def __init__(self):
        super().__init__(FormTestRecommendationsForUserAgent())