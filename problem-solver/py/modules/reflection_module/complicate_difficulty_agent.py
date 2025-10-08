import logging
from typing import List
from sc_client.models import ScAddr, ScTemplate
from sc_client.constants import sc_type
from sc_client.client import search_by_template, generate_by_template, delete_elements

from sc_kpm import ScAgentClassic, ScResult

from sc_kpm.utils.action_utils import (
    finish_action_with_status,
    get_action_arguments
)
from sc_kpm import ScKeynodes

from .additions import get_user_kn_level, update_kn_level, get_system_rating, get_self_rating


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s", datefmt="[%d-%b-%y %H:%M:%S]"
)


class ComplicateDifficultyAgent(ScAgentClassic):
    def __init__(self):
        super().__init__("action_complicate_difficulty")

    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("ComplicateDifficultyAgent finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result
    

    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("ComplicateDifficultyAgent started")

        [user] = get_action_arguments(action_node, 1)

        ratings = (get_system_rating(user), get_self_rating(user))
        this_level = get_user_kn_level(ratings[0])
        more_hard_level = self.get_more_hard_level(this_level)

        if more_hard_level.is_valid():
            for rating in ratings:
                update_kn_level(rating, more_hard_level)
            return ScResult.OK
        
        return ScResult.NO
    

    def get_more_hard_level(self, level: ScAddr) -> ScAddr:
        templ = ScTemplate()
        templ.quintuple(
            level,
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE, "_more_hard_difficulty"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_next_level", sc_type.CONST_NODE_NON_ROLE)
        )

        search_results = search_by_template(templ)
        if search_results:
            return search_results[0].get("_more_hard_difficulty")
        return ScAddr()
