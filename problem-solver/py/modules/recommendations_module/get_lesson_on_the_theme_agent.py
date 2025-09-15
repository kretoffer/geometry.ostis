import logging
from typing import List
from sc_client.models import ScAddr, ScTemplate, ScSet
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
        if self.delete_previous_lessons(user, theme):
            self.set_user_prefering_lesson_materials(user, theme, preferable_content_types, personal_characteristics)

        return ScResult.OK


    def get_user_preferable_content_types(user: ScAddr) -> list[ScAddr]:
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
            (sc_type.CONST_NODE_CLASS, "_content_type")
        )

        search_results = search_by_template(templ)
        content_types = []
        if search_results:
            for content_type_element in content_types:
                content_types.append(content_type_element.get("_content_type"))
        return content_types
    

    def get_user_personal_characteristics(user: ScAddr) -> list[ScAddr]:
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
            (sc_type.CONST_NODE_CLASS, "_characteristic")
        )

        search_results = search_by_template(templ)
        characteristic = []
        if search_results:
            for content_type_element in characteristic:
                characteristic.append(content_type_element.get("_characteristic"))
        return characteristic
    

    def delete_previous_lessons(user: ScAddr, theme: ScAddr) -> bool:
        templ = ScTemplate()
        templ.quintuple(
            user,
            (sc_type.VAR_COMMON_ARC, "_previous_arc") 
            (sc_type.VAR_NODE_STRUCTURE, "_lessons_structure"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_lessons_on_theme", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.quintuple(
            user,
            sc_type.VAR_COMMON_ARC, 
            theme,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_stiding_theme", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.triple(
            "_lessons_structure",
            sc_type.VAR_PERM_POS_ARC,
            theme
        )

        search_results = search_by_template(templ)
        if search_results:
            struct = search_results[0].get("_lessons_structure"),
            previous_arc = search_results[0].get("_previous_arc"),
            return delete_elements(struct, previous_arc)
        return True
    

    def set_user_prefering_lesson_materials(user: ScAddr, theme: ScAddr, 
            content_types: list[ScAddr], personal_characteristics: list[ScAddr]) -> bool:
        templ = ScTemplate()
        templ.quintuple(
            theme,
            sc_type.VAR_COMMON_ARC,
            (sc_type.VAR_NODE, "_lesson_formats_set"),
            sc_type.VAR_PERM_POS_ARC, 
            ScKeynodes("nrel_formats", sc_type.CONST_NODE_NON_ROLE)
        )

        search_results = search_by_template(templ)
        
        if not search_results:
            return ScAddr()
        
        lesson_formats_set = search_results[0].get("_lesson_formats_set")
        lessons = ScSet()
        for lesson_format in content_types:
            templ = ScTemplate()
            templ.triple(
                lesson_formats_set, 
                sc_type.VAR_PERM_POS_ARC,
                (sc_type.VAR_NODE, "_lesson")
            )
            templ.triple(
                lesson_format, 
                sc_type.VAR_PERM_POS_ARC,
                "_lesson"
            )
            for characteristic in personal_characteristics:
                templ.quintuple(
                    "_lesson",
                    sc_type.VAR_PERM_POS_ARC,
                    characteristic,
                    sc_type.VAR_PERM_POS_ARC,
                    ScKeynodes.resolve("rrel_is_available_for", sc_type.CONST_NODE_ROLE)
                )   

        search_results = search_by_template(templ)
        if not search_results:
            return False   
        
        for result in search_results:
            lessons.add(result.get("_lesson"))
        
        templ = ScTemplate()
        templ.quintuple(
            user,
            sc_type.VAR_COMMON_ARC 
            (sc_type.VAR_NODE_STRUCTURE, "_lessons_structure"),
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_lessons_on_theme", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.quintuple(
            user,
            sc_type.VAR_COMMON_ARC, 
            theme,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_stiding_theme", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.triple(
            "_lessons_structure",
            sc_type.VAR_PERM_POS_ARC,
            theme
        )
        templ.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            lessons,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes.resolve("nrel_lessons_on_theme", sc_type.CONST_NODE_NON_ROLE)
        )
        templ.triple(
            "_lessons_structure",
            sc_type.VAR_PERM_POS_ARC,
            lessons
        )

        return generate_by_template(templ)






