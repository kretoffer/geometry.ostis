from sc_client.constants import sc_type
from sc_client.models import ScConstruction, ScAddr
from sc_client.client import generate_elements

from sc_kpm.sc_keynodes import ScKeynodes


def create_action(action: str, *args: ScAddr):
    action_class = ScKeynodes.resolve(action, sc_type.CONST_NODE_CLASS)
    action_initiated = ScKeynodes.resolve("action_initiated", sc_type.CONST_NODE_CLASS)
    constr = ScConstruction()
    constr.create_node(sc_type.CONST_NODE, "action")
    constr.create_edge(sc_type.CONST_PERM_POS_ARC, action_class, "action")
    constr.create_edge(sc_type.CONST_PERM_POS_ARC, ScKeynodes.resolve("action", sc_type.CONST_NODE_CLASS), "action")

    for i, arg in enumerate(args):
        constr.create_edge(sc_type.CONST_PERM_POS_ARC, "action", arg, f"arc_{i+1}")
        constr.create_edge(sc_type.CONST_PERM_POS_ARC, ScKeynodes.rrel_index(i+1), f"arc_{i+1}")

    constr.create_edge(sc_type.CONST_PERM_POS_ARC, action_initiated, "action")
    generate_elements(constr)
