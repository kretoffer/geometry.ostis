import logging
from sc_client.models import ScAddr, ScTemplate
from sc_client.constants import sc_type
from sc_client.client import search_by_template, delete_elements

from sc_kpm import ScAgentClassic, ScResult
from sc_kpm.utils import (
    generate_connector,
    generate_node,
    get_link_content_data
)
from sc_kpm.utils.action_utils import (
    finish_action_with_status,
    get_action_arguments
)
from sc_kpm import ScKeynodes

from typing import Tuple, List

from additions import get_user_passing_test_history, is_question_answer_correct

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s", datefmt="[%d-%b-%y %H:%M:%S]"
)

class FinishTestAgent(ScAgentClassic):
    def __init__(self):
        super().__init__("action_finish_test")

    
    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("FinishTestAgent finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result
    

    def run(self, action: ScAddr) -> ScResult:
        self.logger.info("FinishTestAgent started")

        # rrel_1 -> (action -> user);;
        # rrel_2 -> (action -> test);;
        [user, test] = get_action_arguments(action, 2)
        passing_test_history = get_user_passing_test_history(user, test)

        templ = ScTemplate()
        templ.quintuple(
            passing_test_history,
            (sc_type.VAR_PERM_POS_ARC, "_arc_to_question"),
            sc_type.NODE,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("rrel_1", sc_type.CONST_NODE_ROLE)
        )
        i = search_by_template(templ)[0].get("_arc_to_question")

        score, middle_question_difficulty, worth_studied_themes, well_studied_themes = self.calculate_test_results(i, passing_test_history)

        self.set_user_knowledge_level(user, self.define_user_knowledge_level(score, middle_question_difficulty, worth_studied_themes, well_studied_themes))
        self.set_user_well_studied_themes(user, well_studied_themes)
        self.set_user_worth_studied_themes(user, worth_studied_themes)
    
        self.logger.info("FinishTestAgent: finished successfully")
        return ScResult.OK
    

    def calculate_test_results(self, i: ScAddr, passing_test_history: ScAddr
                        ) -> Tuple[int, int, List[ScAddr], List[ScAddr]]: #score, middle_question_difficulty, worth_studied_themes, well_studied_themes
        themes = []
        results = []

        difficultys = []
        score = 0

        while True:
            templ = ScTemplate()
            templ.triple(
                passing_test_history,
                i,
                (sc_type.NODE, "_question")
            )
            search_results = search_by_template(templ)
            question = search_results[0].get("_question")
            templ.quintuple(
                question,
                sc_type.VAR_PERM_POS_ARC,
                (sc_type.NODE, "_question"),
                sc_type.VAR_PERM_POS_ARC,
                ScKeynodes.resolve("rrel_test_question", sc_type.CONST_NODE_ROLE)
            )
            question_ref = search_by_template(templ)[0].get("_question")

            templ.quintuple(
                question,
                sc_type.VAR_PERM_POS_ARC,
                (sc_type.NODE, "_answer"),
                sc_type.VAR_PERM_POS_ARC,
                ScKeynodes.resolve("rrel_question_answer", sc_type.CONST_NODE_ROLE)
            )
            user_answer = search_by_template(templ)[0].get("_answer")


            # Получение необходимых значений для оценивания
            templ.quintuple(
                question_ref,
                sc_type.COMMON_ARC,
                (sc_type.NODE, "_theme"),
                sc_type.COMMON_ARC,
                ScKeynodes.resolve("nrel_theme", sc_type.CONST_NODE_NON_ROLE)
            )
            theme = search_by_template(templ)[0].get("_theme")
            templ.quintuple(
                question_ref,
                sc_type.COMMON_ARC,
                (sc_type.NODE, "_difficulty"),
                sc_type.COMMON_ARC,
                ScKeynodes.resolve("nrel_difficulty", sc_type.CONST_NODE_NON_ROLE)
            )
            difficulty = int(get_link_content_data(search_by_template(templ)[0].get("_difficulty")))


            is_correct = is_question_answer_correct(user_answer, question)
            if theme in themes:
                j = themes.index(theme)
                results[j] += difficulty if is_correct else -difficulty
            else:
                themes.append(theme)
                results.append(difficulty if is_correct else -difficulty)

            score += difficulty if is_correct else -difficulty
            difficultys.append(difficulty)

            # Нахождение ребра указывающего на следующий вопрос
            templ.quintuple(
                i,
                sc_type.COMMON_ARC,
                (sc_type.VAR_PERM_POS_ARC, "_arc"),
                sc_type.VAR_PERM_POS_ARC,
                ScKeynodes.resolve("nrel_basic_sequence", sc_type.CONST_NODE_NON_ROLE)
            )

            if search_results := search_by_template(templ):
                i = search_results[0].get("_arc")
            else:
                break

        middle_question_difficulty = difficultys[len(difficulty)/2]
        worth_studied_themes = [theme for theme in themes if results[themes.index(theme)] < 10]
        well_studied_themes = [theme for theme in themes if results[themes.index(theme)] > 10]

        return score, middle_question_difficulty, worth_studied_themes, well_studied_themes
    
    def define_user_knowledge_level(score, middle_question_difficulty, worth_studied_themes, well_studied_themes) -> ScAddr:
        #TODO логика определения уровня знаний
        return ScKeynodes.resolve("low_knowledge_level", sc_type.NODE)

    def set_user_worth_studied_themes(user: ScAddr, themes: List[ScAddr]):
        for theme in themes:
            arc = generate_connector(sc_type.COMMON_ARC, user, theme)
            generate_connector(sc_type.VAR_PERM_POS_ARC, ScKeynodes.resolve("nrel_worth_studied_themes", sc_type.NODE_NON_ROLE), arc)


    def set_user_well_studied_themes(user: ScAddr, themes: List[ScAddr]):
        for theme in themes:
            arc = generate_connector(sc_type.COMMON_ARC, user, theme)
            generate_connector(sc_type.VAR_PERM_POS_ARC, ScKeynodes.resolve("nrel_well_studied_themes", sc_type.NODE_NON_ROLE), arc)

    def set_user_knowledge_level(user: ScAddr, knowledge_level: ScAddr):
        nrel_knowledge_level = ScKeynodes.resolve("nrel_knowledge_level", sc_type.NODE_NON_ROLE)
        templ = ScTemplate()
        templ.quintuple(
            user,
            (sc_type.COMMON_ARC, "_arc"),
            sc_type.NODE,
            sc_type.VAR_PERM_POS_ARC,
            nrel_knowledge_level
        )
        if search_results := search_by_template(templ):
            arc = search_results[0].get("_arc")
            delete_elements(arc)
        arc = generate_connector(sc_type.COMMON_ARC, user, knowledge_level)
        generate_connector(sc_type.VAR_PERM_POS_ARC, nrel_knowledge_level, arc)
