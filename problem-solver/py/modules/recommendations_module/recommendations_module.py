from sc_kpm import ScModule
from .form_test_recommendations_for_user_agent import FormTestRecommendationsForUserAgent
from .form_task_recommendations_for_user_agent import FormTaskRecommendationsForUserAgent
from .form_theme_recommendations_for_user_to_study_agent import FormThemeRecommendationsForUserToStudyAgent
from .form_theme_recommendations_for_user_to_solve_test_or_problem_agent import FormThemeRecommendationsForUserToSolveTestOrTaskAgent
from .get_lesson_on_the_theme_agent import GetLessonOnTheThemeAgent

class RecommendationsModule(ScModule):
    def __init__(self):
        super().__init__(
            FormTestRecommendationsForUserAgent(),
            FormTaskRecommendationsForUserAgent(),
            FormThemeRecommendationsForUserToStudyAgent(),
            FormThemeRecommendationsForUserToSolveTestOrTaskAgent(),
            GetLessonOnTheThemeAgent()
        )