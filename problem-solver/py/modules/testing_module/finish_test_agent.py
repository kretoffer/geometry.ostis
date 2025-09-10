import logging
from sc_client.models import ScAddr, ScTemplate
from sc_client.constants import sc_type
from sc_client.client import search_by_template, delete_elements

from sc_kpm import ScAgentClassic, ScResult
from sc_kpm.utils import (
    generate_connector,
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
                        ) -> Tuple[int, int, List[ScAddr], List[ScAddr]]: 
                            #score, middle_question_difficulty, worth_studied_themes, well_studied_themes
        themes = []
        results = []

        difficulties = []
        score = 0

        while True:
            templ = ScTemplate()
            templ.triple(
                passing_test_history,
                i,
                (sc_type.VAR_NODE, "_question")
            )
            search_results = search_by_template(templ)

            question = search_results[0].get("_question")
            templ.quintuple(
                question,
                sc_type.VAR_PERM_POS_ARC,
                (sc_type.VAR_NODE, "_question"),
                sc_type.VAR_PERM_POS_ARC,
                ScKeynodes.resolve("rrel_test_question", sc_type.CONST_NODE_ROLE)
            )
            question_ref = search_by_template(templ)[0].get("_question")

            templ.quintuple(
                question,
                sc_type.VAR_PERM_POS_ARC,
                (sc_type.VAR_NODE, "_answer"),
                sc_type.VAR_PERM_POS_ARC,
                ScKeynodes.resolve("rrel_question_answer", sc_type.CONST_NODE_ROLE)
            )
            user_answer = search_by_template(templ)[0].get("_answer")


            # Получение необходимых значений для оценивания
            templ.quintuple(
                question_ref,
                sc_type.VAR_COMMON_ARC,
                (sc_type.VAR_NODE, "_theme"),
                sc_type.VAR_PERM_POS_ARC,
                ScKeynodes.resolve("nrel_theme", sc_type.CONST_NODE_NON_ROLE)
            )
            theme = search_by_template(templ)[0].get("_theme")
            templ.quintuple(
                question_ref,
                sc_type.VAR_COMMON_ARC,
                (sc_type.VAR_NODE, "_difficulty"),
                sc_type.VAR_PERM_POS_ARC,
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
            difficulties.append(difficulty)

            # Нахождение ребра указывающего на следующий вопрос
            templ.quintuple(
                i,
                sc_type.VAR_COMMON_ARC,
                (sc_type.VAR_PERM_POS_ARC, "_arc"),
                sc_type.VAR_PERM_POS_ARC,
                ScKeynodes.resolve("nrel_basic_sequence", sc_type.CONST_NODE_NON_ROLE)
            )

            if search_results := search_by_template(templ):
                i = search_results[0].get("_arc")
            else:
                break

        middle_question_difficulty = difficulties[len(difficulty)/2]
        worth_studied_themes = [theme for theme in themes if results[themes.index(theme)] < 2]
        well_studied_themes = [theme for theme in themes if results[themes.index(theme)] > 2]

        return score, middle_question_difficulty, worth_studied_themes, well_studied_themes
    

    def define_user_knowledge_level(score, middle_question_difficulty, worth_studied_themes, well_studied_themes) -> ScAddr:
        # Логика определения уровня знаний
        if score >= 85 and middle_question_difficulty >= 4 and len(worth_studied_themes) <= 1: 
            return ScKeynodes.resolve("olimpyc_knowledge_level", sc_type.CONST_NODE)
        if score >= 70 and middle_question_difficulty >= 3.5 and len(worth_studied_themes) <= 3: 
            return ScKeynodes.resolve("good_knowledge_level", sc_type.CONST_NODE)
        if score >= 40 and middle_question_difficulty >= 2.5:
            return ScKeynodes.resolve("normal_knowledge_level", sc_type.CONST_NODE)
        return ScKeynodes.resolve("bad_knowledge_level", sc_type.CONST_NODE)


    def get_system_rating_of_user(self, user: ScAddr) -> ScAddr:
        templ = ScTemplate()
        templ.quintuple(
            user, 
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE_STRUCTURE, "_system_rating"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes("nrel_system_rating", sc_type.CONST_NODE_NON_ROLE)
        )

        search_results = search_by_template(templ)
        if search_results:
            return search_results[0].get("_system_rating")
        return ScAddr()


    def set_user_worth_studied_themes(self, user: ScAddr, themes: List[ScAddr]):
        templ = ScTemplate()
        templ.triple(
            self.get_system_rating_of_user(user),
            sc_type.VAR_PERM_POS_ARC,
            (sc_type.VAR_NODE, "_themes_set")
        )
        templ.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            "_themes_set",
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_worth_studied_themes", sc_type.CONST_NODE_NON_ROLE)
        )

        themes_set = search_by_template(templ)[0].get("_themes_set")

        for theme in themes:
            generate_connector(sc_type.CONST_PERM_POS_ARC, themes_set, theme)


    def set_user_well_studied_themes(self, user: ScAddr, themes: List[ScAddr]):
        templ = ScTemplate()
        templ.triple(
            self.get_system_rating_of_user(user),
            sc_type.VAR_PERM_POS_ARC,
            (sc_type.VAR_NODE, "_themes_set")
        )
        templ.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            "_themes_set",
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_well_studied_themes", sc_type.CONST_NODE_NON_ROLE)
        )

        themes_set = search_by_template(templ)[0].get("_themes_set")

        for theme in themes:
            generate_connector(sc_type.CONST_PERM_POS_ARC, themes_set, theme)


    def set_user_knowledge_level(self, user: ScAddr, knowledge_level: ScAddr):
        system_rating = self.get_system_rating_of_user(user)
        templ = ScTemplate()
        templ.quintuple(
            (sc_type.VAR_NODE, "_knowledge_level_info"),
            sc_type.VAR_ACTUAL_TEMP_POS_ARC,
            system_rating,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes("rrel_student", sc_type.CONST_NODE_ROLE)
        )

        templ.quintuple(
            "_knowledge_level_info",
            (sc_type.VAR_ACTUAL_TEMP_POS_ARC, "_arc_to_knowledge_level"),
            (sc_type.VAR_NODE, "_knowledge_level"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes("rrel_knowledge_level", sc_type.CONST_NODE_ROLE)
        )
        search_results = search_by_template(templ)
        delete_elements(search_results[0].get("_arc_to_knowledge_level"))
        arc = generate_connector(sc_type.CONST_ACTUAL_TEMP_POS_ARC, search_results[0].get("_knowledge_level_info"), knowledge_level)
        generate_connector(sc_type.CONST_PERM_POS_ARC, ScKeynodes("rrel_knowledge_level", sc_type.CONST_NODE_ROLE), arc)
