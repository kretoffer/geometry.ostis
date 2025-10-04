import logging
from typing import List
from sc_client.models import ScAddr, ScTemplate
from sc_client.constants import sc_type
from sc_client.client import search_by_template, generate_by_template, delete_elements

from sc_kpm import ScAgentClassic, ScResult
from sc_kpm.sc_sets import ScSet
from sc_kpm.utils import (
    generate_connector,
    generate_node,
    get_link_content_data
)
from sc_kpm.utils.action_utils import (
    finish_action_with_status,
    get_action_arguments,
    generate_action_result
)
from sc_kpm import ScKeynodes


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s", datefmt="[%d-%b-%y %H:%M:%S]"
)


class GetLessonOnTheThemeAgent(ScAgentClassic):


    def __init__(self):
        super().__init__("action_get_lesson_on_theme")
    
    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("GetLessonOnTheThemeAgent finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result


    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("GetLessonOnTheThemeAgent started")

        [user, theme] = get_action_arguments(action_node, 2)


        preferable_content_types = self.get_user_preferable_content_types(user)
        personal_characteristics = self.get_user_personal_characteristics(user)
        lessons = self.set_user_prefering_lesson_materials(theme, preferable_content_types, personal_characteristics)

        if lessons:
            self.logger.info("GetLessonOnTheThemeAgent: recommendations are generated")
            generate_action_result(action_node, lessons)
            return ScResult.OK

        return ScResult.NO


    def get_user_preferable_content_types(self, user: ScAddr) -> list[ScAddr]:
        templ = ScTemplate()
        templ.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE, "_preferencies_set"),
            sc_type.VAR_PERM_POS_ARC, 
            ScKeynodes.resolve("nrel_preferable_content_types", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.triple(
            "_preferencies_set",
            sc_type.VAR_PERM_POS_ARC,
            (sc_type.VAR_NODE_CLASS, "_content_type")
        )

        search_results = search_by_template(templ)
        content_types = []
        for el in search_results:
            content_types.append(el.get("_content_type"))
        return content_types
    

    def get_user_personal_characteristics(self, user: ScAddr) -> list[ScAddr]:
        templ = ScTemplate()
        templ.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE, "_characteristics_set"),
            sc_type.VAR_PERM_POS_ARC, 
            ScKeynodes.resolve("nrel_personal_characteristics", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.triple(
            "_characteristics_set",
            sc_type.VAR_PERM_POS_ARC,
            (sc_type.VAR_NODE_CLASS, "_characteristic")
        )

        search_results = search_by_template(templ)
        characteristic = []
        for el in search_results:
            characteristic.append(el.get("_characteristic"))
        return characteristic
    

    def set_user_prefering_lesson_materials(self, theme: ScAddr, 
            content_types: list[ScAddr], personal_characteristics: list[ScAddr]) -> ScAddr:
        templ = ScTemplate()
        templ.quintuple(
            theme,
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE, "_lessons_set"),
            sc_type.VAR_PERM_POS_ARC, 
            ScKeynodes.resolve("nrel_lessons", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.triple(
            "_lessons_set",
            sc_type.VAR_PERM_POS_ARC,
            (sc_type.VAR_NODE, "_lesson")
        )
        search_results_without_format = search_by_template(templ)
        if not search_results_without_format:
            return ScAddr()
        search_results_without_characteristic = []
        ideal_search_results = []

        lessons_set = search_results_without_format[0].get("_lessons_set")

        for lesson_format in content_types:
            templ = ScTemplate()
            templ.triple(
                lessons_set,
                sc_type.VAR_PERM_POS_ARC,
                (sc_type.VAR_NODE, "_lesson")
            )
            templ.triple(
                lesson_format, 
                sc_type.VAR_PERM_POS_ARC,
                "_lesson"
            )

            search_results = search_by_template(templ)
            if not search_results:
                search_results_without_characteristic.extend(search_results)
                continue

            for characteristic in personal_characteristics:
                templ.quintuple(
                    "_lesson",
                    sc_type.VAR_PERM_POS_ARC,
                    characteristic,
                    sc_type.VAR_PERM_POS_ARC,
                    ScKeynodes.resolve("rrel_is_available_for", sc_type.CONST_NODE_ROLE)
                )

            ideal_search_results.extend(search_by_template(templ))

        if ideal_search_results:
            search_results = ideal_search_results
        elif search_results_without_characteristic:
            search_results = search_results_without_characteristic
        elif search_results_without_format:
            search_results = search_results_without_format
        else:
            return ScAddr()
        
        lessons = ScSet()
        for search_result in search_results:
            lessons.add(search_result.get("_lesson"))
        
        return lessons.set_node






