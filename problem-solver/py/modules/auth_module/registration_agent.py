import logging
from sc_client.models import ScAddr, ScTemplate, ScConstruction
from sc_client.constants import sc_type
from sc_client.client import search_by_template, generate_elements

from sc_kpm import ScAgentClassic, ScResult
from sc_kpm.utils.action_utils import (
    finish_action_with_status,
    get_action_arguments
)
from sc_kpm import ScKeynodes


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s", datefmt="[%d-%b-%y %H:%M:%S]"
)


class RegistrationAgent(ScAgentClassic):
    def __init__(self):
        super().__init__("action_reg_user")

    def on_event(self, action_class: ScAddr, arc: ScAddr, action: ScAddr) -> ScResult:
        result = self.run(action)
        is_successful = result == ScResult.OK
        finish_action_with_status(action, is_successful)
        self.logger.info("RegistrationAgent finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result

    def run(self, action: ScAddr) -> ScResult:
        self.logger.info("RegistrationAgent started")
        
        # rrel_1 -> (action -> user_id_link);;
        # rrel_2 -> (action -> user_class_link);;
        # rrel_3 -> (action -> user_name_link);;
        # rrel_4 -> (action -> self_knowledge_level);;
        [user_id_link, user_class_link, user_name_link, self_knowledge_level] = get_action_arguments(action, 4)

        if self.get_user(user_id_link):
            return ScResult.OK
        
        constr = ScConstruction()

        # user
        constr.generate_node(sc_type.CONST_NODE, "user")
        constr.generate_connector(sc_type.CONST_PERM_POS_ARC, ScKeynodes.resolve("concept_student", sc_type.VAR_NODE_CLASS), "user")

        # user id
        constr.generate_connector(sc_type.CONST_COMMON_ARC, "user", user_id_link, "arc_to_user_id_link")
        constr.generate_connector(sc_type.CONST_PERM_POS_ARC, ScKeynodes.resolve("nrel_tg_id", sc_type.VAR_NODE_NON_ROLE), "arc_to_user_id_link")

        # user class
        constr.generate_connector(sc_type.CONST_COMMON_ARC, "user", user_class_link, "arc_to_user_class_link")
        constr.generate_connector(sc_type.CONST_PERM_POS_ARC, ScKeynodes.resolve("nrel_class", sc_type.VAR_NODE_NON_ROLE), "arc_to_user_class_link")

        # user name
        constr.generate_connector(sc_type.CONST_COMMON_ARC, "user", user_name_link, "arc_to_user_name_link")
        constr.generate_connector(sc_type.CONST_PERM_POS_ARC, ScKeynodes.resolve("nrel_name", sc_type.VAR_NODE_NON_ROLE), "arc_to_user_name_link")

        sets = [
            "preferable_content_types",
            "personal_characteristics",
            "solved_tasks",
            "not_solved_tasks",
            "studied_themes",
            "achievements"
        ]

        for set_name in sets:
            constr.generate_node(sc_type.CONST_NODE_TUPLE, set_name)
            constr.generate_connector(sc_type.CONST_COMMON_ARC, "user", set_name, f"arc_to_{set_name}")
            constr.generate_connector(sc_type.CONST_PERM_POS_ARC, ScKeynodes.resolve(f"nrel_{set_name}", sc_type.VAR_NODE_NON_ROLE), f"arc_to_{set_name}")

        # ratings
        for rating in ["self", "system"]:
            constr.generate_node(sc_type.CONST_NODE_STRUCTURE, rating)
            constr.generate_connector(sc_type.CONST_COMMON_ARC, "user", rating, f"user2{rating}_arc")
            constr.generate_connector(sc_type.CONST_PERM_POS_ARC, rating, "user")

            constr.generate_connector(sc_type.CONST_PERM_POS_ARC, ScKeynodes.resolve(f"nrel_{rating}_rating", sc_type.CONST_NODE_NON_ROLE), f"user2{rating}_arc")

            constr.generate_node(sc_type.CONST_NODE, f"{rating}_main")
            constr.generate_connector(sc_type.CONST_PERM_POS_ARC, rating, f"{rating}_main", f"set2{rating}_main_arc")
            constr.generate_connector(sc_type.CONST_TEMP_POS_ARC, f"{rating}_main", "user", f"{rating}_main2user_arc")
            constr.generate_connector(sc_type.CONST_PERM_POS_ARC, rating, f"{rating}_main2user_arc")


            constr.generate_connector(sc_type.CONST_PERM_POS_ARC, rating, ScKeynodes.resolve("rrel_theme", sc_type.VAR_NODE_ROLE))

            constr.generate_node(sc_type.CONST_NODE_TUPLE, f"{rating}_themes_set")
            constr.generate_connector(sc_type.CONST_PERM_POS_ARC, rating, f"{rating}_themes_set")
            constr.generate_connector(sc_type.CONST_TEMP_POS_ARC, f"{rating}_main", f"{rating}_themes_set", f"main_{rating}2themes_set_arc")
            constr.generate_connector(sc_type.CONST_PERM_POS_ARC, rating, f"main_{rating}2themes_set_arc")
            constr.generate_connector(sc_type.CONST_PERM_POS_ARC, ScKeynodes.resolve("rrel_theme", sc_type.VAR_NODE_ROLE), f"main_{rating}2themes_set_arc", f"arc_rrel_theme2themes_{rating}_set")
            constr.generate_connector(sc_type.CONST_PERM_POS_ARC, rating, f"arc_rrel_theme2themes_{rating}_set")

            constr.generate_connector(sc_type.CONST_PERM_POS_ARC, rating, ScKeynodes.resolve("rrel_student", sc_type.CONST_NODE_ROLE))
            constr.generate_connector(sc_type.CONST_PERM_POS_ARC, ScKeynodes.resolve("rrel_student", sc_type.CONST_NODE_ROLE), f"{rating}_main2user_arc", f"rrel_studen2user_{rating}_arc")
            constr.generate_connector(sc_type.CONST_PERM_POS_ARC, rating, f"rrel_studen2user_{rating}_arc")

            constr.generate_connector(sc_type.CONST_PERM_POS_ARC, rating, ScKeynodes.resolve("rrel_assesser", sc_type.CONST_NODE_ROLE))
            constr.generate_connector(sc_type.CONST_PERM_POS_ARC, ScKeynodes.resolve("rrel_assesser", sc_type.CONST_NODE_ROLE), f"{rating}_main2user_arc", f"assser2arc2user_{rating}_arc")
            constr.generate_connector(sc_type.CONST_PERM_POS_ARC, rating, f"assser2arc2user_{rating}_arc")

            for theme_type in ["well", "worth"]:
                constr.generate_node(sc_type.CONST_NODE_TUPLE, f"{rating}_{theme_type}_themes_set")
                constr.generate_connector(sc_type.CONST_PERM_POS_ARC, rating, f"{rating}_{theme_type}_themes_set")
                constr.generate_connector(sc_type.CONST_COMMON_ARC, "user", f"{rating}_{theme_type}_themes_set", f"user2_{rating}_{theme_type}_set_arc")
                constr.generate_connector(sc_type.CONST_PERM_POS_ARC, rating, f"user2_{rating}_{theme_type}_set_arc")

                constr.generate_connector(sc_type.CONST_PERM_POS_ARC, rating, ScKeynodes.resolve(f"nrel_{theme_type}_studied_themes", sc_type.CONST_NODE_NON_ROLE))
                constr.generate_connector(sc_type.CONST_PERM_POS_ARC, ScKeynodes.resolve(f"nrel_{theme_type}_studied_themes", sc_type.CONST_NODE_NON_ROLE), f"user2_{rating}_{theme_type}_set_arc", f"{rating}_{theme_type}2set_arc_arc")
                constr.generate_connector(sc_type.CONST_PERM_POS_ARC, rating, f"{rating}_{theme_type}2set_arc_arc")

            constr.generate_connector(sc_type.CONST_PERM_POS_ARC, rating, ScKeynodes.resolve("nrel_user_knowledge_level", sc_type.CONST_NODE_NON_ROLE))
            constr.generate_connector(sc_type.CONST_TEMP_POS_ARC, ScKeynodes.resolve("nrel_user_knowledge_level", sc_type.CONST_NODE_NON_ROLE), f"{rating}_main", f"{rating}_kn_level2main")
            constr.generate_connector(sc_type.CONST_PERM_POS_ARC, rating, f"{rating}_kn_level2main")
            constr.generate_connector(sc_type.CONST_PERM_POS_ARC, rating, ScKeynodes.resolve("rrel_knowledge_level", sc_type.CONST_NODE_ROLE))

        # self rating
        constr.generate_connector(sc_type.CONST_PERM_POS_ARC, "self", self_knowledge_level)
        constr.generate_connector(sc_type.CONST_TEMP_POS_ARC, "self_main", self_knowledge_level, "self_main2kn_level_arc")
        constr.generate_connector(sc_type.CONST_PERM_POS_ARC, "self", "self_main2kn_level_arc")
        constr.generate_connector(sc_type.CONST_PERM_POS_ARC, ScKeynodes.resolve("rrel_knowledge_level", sc_type.CONST_NODE_ROLE), "self_main2kn_level_arc", "rrel_kn_level2arc2kn_level")
        constr.generate_connector(sc_type.CONST_PERM_POS_ARC, "self", "rrel_kn_level2arc2kn_level")

        generate_elements(constr)
        return ScResult.OK
    

    def get_user(self, user_id_link: ScAddr) -> ScAddr:
        templ = ScTemplate()
        templ.quintuple(
            (sc_type.VAR_NODE, "user"),
            sc_type.VAR_COMMON_ARC,
            user_id_link,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_tg_id", sc_type.NODE_NON_ROLE)
        )
        if search_results := search_by_template(templ):
            return search_results[0].get("user")
        return ScAddr()
