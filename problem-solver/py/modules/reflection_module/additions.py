from sc_client.models import ScAddr, ScTemplate
from sc_client.constants import sc_type
from sc_client.client import search_by_template, delete_elements, generate_by_template

from sc_kpm import ScKeynodes


def get_user_kn_level(rating: ScAddr) -> ScAddr:
    templ = ScTemplate()
    templ.quintuple(
        ScKeynodes.resolve("nrel_user_knowledge_level", sc_type.CONST_NODE_NON_ROLE),
        sc_type.VAR_ACTUAL_TEMP_POS_ARC,
        (sc_type.VAR_NODE, "main"),
        sc_type.VAR_PERM_POS_ARC,
        rating
    )
    templ.quintuple(
        "main",
        sc_type.VAR_ACTUAL_TEMP_POS_ARC,
        (sc_type.VAR_NODE, "knowledge_level"),
        sc_type.VAR_PERM_POS_ARC,
        ScKeynodes.resolve("rrel_knowledge_level", sc_type.CONST_NODE_ROLE)
    )
    knowledge_level = search_by_template(templ)[0].get("knowledge_level")
    return knowledge_level


def get_rating(user: ScAddr, relation: ScAddr) -> ScAddr:
    templ = ScTemplate()
    templ.quintuple(
        user,
        sc_type.COMMON_ARC,
        (sc_type.VAR_NODE_STRUCTURE, "_rating"),
        sc_type.VAR_PERM_POS_ARC,
        relation
    )

    search_results = search_by_template(templ)
    if search_results:
        return search_results[0].get("_rating")
    return ScAddr()


def get_self_rating(user: ScAddr) -> ScAddr:
    return get_rating(user, ScKeynodes.resolve("nrel_self_rating", sc_type.CONST_NODE_NON_ROLE))

def get_system_rating(user: ScAddr) -> ScAddr:
    return get_rating(user, ScKeynodes.resolve("nrel_system_rating", sc_type.CONST_NODE_NON_ROLE))


def update_kn_level(rating: ScAddr, new_kn_level: ScAddr):
    templ = ScTemplate()
    templ.quintuple(
        ScKeynodes.resolve("nrel_user_knowledge_level", sc_type.CONST_NODE_NON_ROLE),
        sc_type.VAR_ACTUAL_TEMP_POS_ARC,
        (sc_type.VAR_NODE, "main"),
        sc_type.VAR_PERM_POS_ARC,
        rating
    )
    templ.quintuple(
        "main",
        (sc_type.VAR_ACTUAL_TEMP_POS_ARC, "arc_to_kn_level"),
        (sc_type.VAR_NODE, "knowledge_level"),
        sc_type.VAR_PERM_POS_ARC,
        ScKeynodes.resolve("rrel_knowledge_level", sc_type.CONST_NODE_ROLE)
    )
    search_result = search_by_template(templ)[0]
    delete_elements(search_result.get("arc_to_kn_level"))

    gen_templ = ScTemplate()
    gen_templ.quintuple(
        ScKeynodes.resolve("nrel_user_knowledge_level", sc_type.CONST_NODE_NON_ROLE),
        sc_type.VAR_ACTUAL_TEMP_POS_ARC,
        (sc_type.VAR_NODE, "main"),
        sc_type.VAR_PERM_POS_ARC,
        rating
    )
    gen_templ.quintuple(
        "main",
        sc_type.VAR_ACTUAL_TEMP_POS_ARC,
        new_kn_level,
        sc_type.VAR_PERM_POS_ARC,
        ScKeynodes.resolve("rrel_knowledge_level", sc_type.CONST_NODE_ROLE)
    )
    generate_by_template(gen_templ)