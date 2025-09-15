import logging
from typing import List
from sc_client.models import ScAddr, ScTemplate, ScSet, ScLinkContent, ScLinkContentType
from sc_client.constants import sc_type
from sc_client.client import search_by_template, generate_by_template, delete_elements,  search_links_by_contents

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


class SetAchievementForStreakAgent(ScAgentClassic):


    def __init__(self):
        super().__init__("action_set_achievement_for_streak")
    
    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("SetAchievementForStreakAgent finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result


    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("SetAchievementForStreakAgent started")

        user = get_action_arguments(action_node, 1)

        streak = self.get_user_streak(user)
        all_user_achievements = self.get_user_achievements(user)

        self.set_achievement_for_streak(user, all_user_achievements, streak)


        return ScResult.OK
    

    def get_user_streak(user: ScAddr) -> int:
        templ = ScTemplate()
        templ.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE_LINK, "_link"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_streak", sc_type.CONST_NODE_NON_ROLE)
        )
        search_results = search_by_template(templ)
        if search_results:
            return int(get_link_content(search_results[0].get("_link")))
        return -1
        

    def get_user_achievements(user: ScAddr) -> ScAddr:
        templ = ScTemplate()
        templ.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE, "_achievements_set"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_achievements", sc_type.CONST_NODE_NON_ROLE)
        )
        search_results = search_by_template(templ)
        if search_results:
            return search_results[0].get("_achievements_set")
        return ScAddr()
    

    def set_achievement_for_streak(user: ScAddr, all_user_achievements: ScAddr, streak: int) -> bool:
        def get_achievement_for_streak(streak: int) -> ScAddr:
            searched_links = search_links_by_contents(streak, ScLinkContentType.INT)
            for searched_link in searched_links:
                templ = ScTemplate()
                templ.quintuple(
                    (sc_type.CONST_NODE, "_achievement"),
                    sc_type.VAR_COMMON_ARC,
                    searched_link,
                    sc_type.VAR_PERM_POS_ARC,
                    ScKeynodes.resolve("nrel_streak_requirements", sc_type.CONST_NODE_NON_ROLE)
                )
                templ.triple(
                    ScKeynodes.resolve("concept_achievement", sc_type.CONST_NODE_CLASS),
                    sc_type.VAR_PERM_POS_ARC,
                    "_achievement"
                )
                search_results = search_by_template(templ)
                if search_results:
                    return search_results[0].get("_achievement")
            return ScAddr()
        

        achievement = get_achievement_for_streak(streak)
        if not achievement.is_valid():
            return False
        
        templ = ScTemplate()
        templ.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE, "_achievements_set"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_achievements", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.triple(
            all_user_achievements,
            sc_type.VAR_PERM_POS_ARC,
            achievement
        )

        if not search_by_template(templ):
            return generate_by_template(templ)
        return True
        

            

            

