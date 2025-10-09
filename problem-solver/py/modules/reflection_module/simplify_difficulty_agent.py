import logging
from sc_client.models import ScAddr, ScTemplate
from sc_client.constants import sc_type
from sc_client.client import search_by_template

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
        self.logger.info("SimplifyDifficultyAgent started")

        [user] = get_action_arguments(action_node, 1)

        ratings = (get_system_rating(user), get_self_rating(user))
        this_level = get_user_kn_level(ratings[0])
        more_simple_level = self.get_more_simple_level(this_level)

        if more_simple_level.is_valid():
            for rating in ratings:
                update_kn_level(rating, more_simple_level)
            return ScResult.OK
        
        return ScResult.NO

    
    def get_more_simple_level(self, this_level: ScAddr) -> ScAddr:
        templ = ScTemplate()
        templ.quintuple(
            (sc_type.VAR_NODE, "_more_simple_difficulty"),
            sc_type.VAR_COMMON_ARC,
            this_level,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_next_level", sc_type.CONST_NODE_NON_ROLE)
        )

        search_results = search_by_template(templ)
        if search_results:
            return search_results[0].get("_more_simple_difficulty")
        return ScAddr()
