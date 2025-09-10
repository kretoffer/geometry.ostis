import logging
from typing import List
from sc_client.models import ScAddr, ScTemplate, ScLinkContent, ScLinkContentType
from sc_client.constants import sc_type
from sc_client.client import search_by_template, generate_by_template, delete_elements

from sc_kpm import ScAgentClassic, ScResult
from sc_kpm.sc_sets import ScSet
from sc_kpm.utils import (
    generate_connector,
    generate_node,
    get_link_content
)
from sc_kpm.utils.action_utils import (
    finish_action_with_status,
    get_action_arguments
)
from sc_kpm import ScKeynodes



logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s", datefmt="[%d-%b-%y %H:%M:%S]"
)


class SimplifyDifficultyAgent(ScAgentClassic):
    def __init__(self):
        super().__init__("action_simplify_difficulty")

    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("SimplifyDifficultyAgent finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result
    

    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("CompareRatingOfProgressAgent started")

        user = get_action_arguments(action_node, 1)


        this_difficulty =  self.get_difficulty_of_questiions(user)

        more_simple_difficulty = self.get_more_simple_level(this_difficulty)

        if more_simple_difficulty.is_valid():
            self.simplify_difficulty(user, more_simple_difficulty)

        return ScResult.OK



    def get_difficulty_of_questiions(user: ScAddr) -> ScAddr:
        templ = ScTemplate()
        templ.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            (sc_type.CONST_NODE, "_user_difficulty"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_difficulty_of_questions", sc_type.CONST_NODE_NON_ROLE)
        )

        search_results = search_by_template(templ)
        if search_results:
            return search_results[0].get("_user_difficulty")
        return ScAddr()
    
    def get_more_simple_level(this_difficulty: ScAddr) -> ScAddr:
        templ = ScTemplate()
        templ.quintuple(
            this_difficulty,
            sc_type.VAR_COMMON_ARC,
            (sc_type.CONST_NODE, "_more_simple_difficulty"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_more_simple_level", sc_type.CONST_NODE_NON_ROLE)
        )

        search_results = search_by_template(templ)
        if search_results:
            return search_results[0].get("_more_simple_difficulty")
        return ScAddr()
    

    def simplify_difficulty(user: ScAddr, new_difficulty: ScAddr) -> bool:
        templ = ScTemplate()
        templ.quintuple(
            user,
            (sc_type.VAR_COMMON_ARC, "_previous_arc"),
            (sc_type.CONST_NODE, "_previous_difficulty"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_difficulty_of_questions", sc_type.CONST_NODE_NON_ROLE)
        )

        search_results = search_by_template(templ)
        if not search_results:
            return False
        
        previous_arc = search_results[0].get("_previous_arc")
        previous_difficulty = search_results[0].get("_previous_difficulty")

        delete_elements(previous_arc, previous_difficulty)

        templ_for_generating = ScTemplate()
        templ_for_generating.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            new_difficulty,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_difficulty_of_questions", sc_type.CONST_NODE_NON_ROLE)
        )