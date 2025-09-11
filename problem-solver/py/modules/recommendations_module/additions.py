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


def get_all_stidied_themes(user: ScAddr) -> list[ScAddr]:
        templ = ScTemplate()
        templ.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE, "_stidied_themes_set"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_studied_themes", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.triple(
            "_stidied_themes_set",
            sc_type.VAR_PERM_POS_ARC,
            (sc_type.VAR_NODE, "_theme")
        )

        search_results = search_by_template(templ)
        themes = []
        if search_results:
            for result in search_results:
                themes.append(result.get("_theme"))

        return themes



def get_middle_tasks_solutions(user: ScAddr, theme: ScAddr) -> float:
        templ = ScTemplate()
        templ.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE, "_solutions_set"),
            sc_type.VAR_PERM_POS_ARC, 
            ScKeynodes.resolve("nrel_solved_tasks", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.triple(
            "_solutions_set",
            sc_type.VAR_PERM_POS_ARC,
            (sc_type.VAR_NODE, "_task")
        )
        templ.quintuple(
            "_task",
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE, "_solution_info"),
            sc_type.VAR_ACTUAL_TEMP_POS_ARC,
            ScKeynodes.resolve("nrel_user_solution", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.triple(
            "_solution_info",
            sc_type.VAR_UNCOMMON_ARC,
            (sc_type.VAR_NODE_STRUCTURE, "_solution_struct")
        )
        templ.triple(
            "_solution_struct",
            sc_type.VAR_PERM_POS_ARC,
            (sc_type.VAR_NODE, "_action_solve_task")
        )
        templ.triple(
            ScKeynodes.resolve("action_solve_task", sc_type.CONST_NODE_CLASS),
            sc_type.VAR_PERM_POS_ARC,
            "_action_solve_task"
        )
        templ.quintuple(
            "_action_solve_task",
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE, "_result_info"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_result", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.quintuple(
            "_result_info",
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE_LINK, "_correctness"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_correctness", sc_type.CONST_NODE_NON_ROLE)
        )


        search_results = search_by_template(templ)
        all_tasks_solutions = []
        if search_results:
            for result in search_results:
                all_tasks_solutions.append(float(get_link_content(result.get("_correctness"))))

            return sum(all_tasks_solutions) / len(all_tasks_solutions)
        
        return -1.0