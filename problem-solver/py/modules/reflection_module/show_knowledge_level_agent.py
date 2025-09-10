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


class ShowKnowledgeLevelAgent(ScAgentClassic):
    def __init__(self):
        super().__init__("action_show_knowledge_level")


    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("ShowKnowledgeLevelAgent finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result
    

    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("CompareRatingOfProgressAgent started")

        user = get_action_arguments(action_node, 1)

        system_rating = self.get_rating(
            user,
            ScKeynodes.resolve("nrel_system_rating", sc_type.CONST_NODE_NON_ROLE)
        )

        user_knowledge_level = self.get_knowledge_level(system_rating, user)

        message = f"Ваш уровень знаний {self.get_knowledge_level(user_knowledge_level)}."


        # TODO связать с тг-ботом

        return ScResult.OK


    
    def get_rating(user: ScAddr, relation: ScAddr) -> ScAddr:
        templ = ScTemplate()
        templ.quintuple(
            user,
            sc_type.COMMON_ARC,
            (sc_type.VAR_NODE_STRUCTURE, "_rating"),
            sc_type.VAR_PERM_POS_ARC,
            relation
        )

        search_results = search_by_template()
        if search_results:
            return search_results[0].get("_rating")
        return ScAddr()


    
    def get_knowledge_level(rating: ScAddr, user: ScAddr) -> ScAddr:
        templ = ScTemplate()
        templ.quintuple(
            (sc_type.VAR_NODE, "_knowledge_level_info"),
            sc_type.VAR_ACTUAL_TEMP_POS_ARC,
            user,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("rrel_student", sc_type.VAR_NODE_ROLE)
        )
        templ.quintuple(
            "_knowledge_level_info",
            sc_type.VAR_ACTUAL_TEMP_POS_ARC,
            (sc_type.CONST_NODE, "_knowledge_level"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("rrel_knowledge_level", sc_type.VAR_NODE_ROLE)
        )
        templ.triple(
            rating,
            sc_type.VAR_PERM_POS_ARC,
            "_knowledge_level"
        )

        search_results = search_by_template(templ)
        if search_results:
            return search_results[0].get("_knowledge_level")
        return ScAddr()
    

    def get_main_idtf(this_node: ScAddr) -> str:
        templ = ScTemplate()
        templ.quintuple(
            this_node,
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE_LINK, "_link"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_main_idtf", sc_type.CONST_NODE_NON_ROLE)
        )

        search_results = search_by_template(templ)
        if search_results:
            return str(get_link_content(search_results[0].get("_link"))[0])
        return ""