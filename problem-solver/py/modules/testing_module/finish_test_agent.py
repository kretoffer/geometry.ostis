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
from sc_kpm.utils.action_utils import generate_action_result
from sc_kpm.sc_sets import ScSet

from typing import Tuple, List

from .additions import get_user_passing_test_history, is_question_answer_correct, is_diagnostic

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

        score, middle_question_difficulty, worth_studied_themes, well_studied_themes = self.calculate_test_results(passing_test_history)

        kn_level = self.define_user_knowledge_level(score, middle_question_difficulty, worth_studied_themes, well_studied_themes)
        if is_diagnostic(test):
            self.set_user_knowledge_level(user, kn_level)
        self.set_user_well_studied_themes(user, well_studied_themes)
        self.set_user_worth_studied_themes(user, worth_studied_themes)

        generate_action_result(action, kn_level)
    
        self.logger.info("FinishTestAgent: finished successfully")
        return ScResult.OK
    

    def calculate_test_results(self, passing_test_history: ScAddr
                        ) -> Tuple[int, int, List[ScAddr], List[ScAddr]]: 
                            #score, middle_question_difficulty, worth_studied_themes, well_studied_themes
        themes = []
        results = []

        difficulties = []
        score = 0

        history = list(ScSet(set_node=passing_test_history).elements_set)
        for el in history:
            question_ref, user_answer, difficulty, theme = self.get_question_info(el)

            is_correct = is_question_answer_correct(user_answer, question_ref)
            if theme in themes:
                j = themes.index(theme)
                results[j] += difficulty if is_correct else -difficulty
            else:
                themes.append(theme)
                results.append(difficulty if is_correct else -difficulty)

            score += difficulty if is_correct else -difficulty
            difficulties.append(difficulty)

        index = len(difficulties)/2
        if index % 2 == 1:
            middle_question_difficulty = difficulties[int(index)+1]
        else:
            middle_question_difficulty = sum(difficulties[int(index):(int(index)+2)])/2
        worth_studied_themes = [theme for theme in themes if results[themes.index(theme)] < 2]
        well_studied_themes = [theme for theme in themes if results[themes.index(theme)] > 2]

        return score, middle_question_difficulty, worth_studied_themes, well_studied_themes
    

    def get_question_info(self, question: ScAddr):
        templ = ScTemplate()
        templ.quintuple(
            question,
            sc_type.VAR_PERM_POS_ARC,
            (sc_type.VAR_NODE, "_answer"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("rrel_question_answer", sc_type.VAR_NODE_ROLE)
        )
        user_answer = search_by_template(templ)[0].get("_answer")
        templ = ScTemplate()
        templ.quintuple(
            question,
            sc_type.VAR_PERM_POS_ARC,
            (sc_type.VAR_NODE, "_question_ref"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("rrel_test_question", sc_type.VAR_NODE_ROLE)
        )
        templ.quintuple(
            "_question_ref",
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE, "_theme"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_theme", sc_type.VAR_NODE_NON_ROLE)
        )
        templ.quintuple(
            "_question_ref",
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE_LINK, "_difficulty"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_difficulty", sc_type.VAR_NODE_NON_ROLE)
        )
        search_results = search_by_template(templ)

        question_ref = search_results[0].get("_question_ref")
        diff = search_results[0].get("_difficulty")
        theme = search_results[0].get("_theme")

        difficulty = int(get_link_content_data(diff))
        return question_ref, user_answer, difficulty, theme
    

    def define_user_knowledge_level(self, score, middle_question_difficulty, worth_studied_themes, well_studied_themes) -> ScAddr:
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
            ScKeynodes.resolve("nrel_system_rating", sc_type.CONST_NODE_NON_ROLE)
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

        templ.triple_list[:-2]
        templ.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            "_themes_set",
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_well_studied_themes", sc_type.CONST_NODE_NON_ROLE)
        )

        for theme in themes:
            generate_connector(sc_type.CONST_PERM_POS_ARC, themes_set, theme)
            templ.triple(
                "_themes_set",
                (sc_type.VAR_PERM_POS_ARC, "_arc"),
                theme
            )
            if search_results := search_by_template(templ):
                delete_elements(search_results[0].get("_arc"))
            templ.triple_list[:-1]


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

        templ.triple_list[:-2]
        templ.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            "_themes_set",
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_worth_studied_themes", sc_type.CONST_NODE_NON_ROLE)
        )

        for theme in themes:
            generate_connector(sc_type.CONST_PERM_POS_ARC, themes_set, theme)
            templ.triple(
                "_themes_set",
                (sc_type.VAR_PERM_POS_ARC, "_arc"),
                theme
            )
            if search_results := search_by_template(templ):
                delete_elements(search_results[0].get("_arc"))
            templ.triple_list[:-1]


    def set_user_knowledge_level(self, user: ScAddr, knowledge_level: ScAddr):
        system_rating = self.get_system_rating_of_user(user)
        templ = ScTemplate()
        templ.quintuple(
            ScKeynodes.resolve("nrel_user_knowledge_level", sc_type.CONST_NODE_NON_ROLE),
            sc_type.VAR_ACTUAL_TEMP_POS_ARC,
            (sc_type.VAR_NODE, "main"),
            sc_type.VAR_PERM_POS_ARC,
            system_rating
        )
        templ.quintuple(
            "main",
            (sc_type.VAR_ACTUAL_TEMP_POS_ARC, "_arc_to_knowledge_level"),
            (sc_type.VAR_NODE, "knowledge_level"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("rrel_knowledge_level", sc_type.CONST_NODE_ROLE)
        )
        templ.triple(
            system_rating,
            (sc_type.VAR_PERM_POS_ARC, "_arc_from_rating"),
            "knowledge_level"
        )
        
        if search_results := search_by_template(templ):
            delete_elements(search_results[0].get("_arc_to_knowledge_level"))
            delete_elements(search_results[0].get("_arc_from_rating"))
            arc = generate_connector(sc_type.CONST_ACTUAL_TEMP_POS_ARC, search_results[0].get("main"), knowledge_level)
            arc_2 = generate_connector(sc_type.CONST_PERM_POS_ARC, ScKeynodes.resolve("rrel_knowledge_level", sc_type.CONST_NODE_ROLE), arc)

            generate_connector(sc_type.CONST_PERM_POS_ARC, system_rating, knowledge_level)
            generate_connector(sc_type.CONST_PERM_POS_ARC, system_rating, arc)
            generate_connector(sc_type.CONST_PERM_POS_ARC, system_rating, arc_2)
