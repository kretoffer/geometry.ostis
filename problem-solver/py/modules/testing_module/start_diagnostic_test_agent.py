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

from random import choice

from utils.create_action import create_action

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s", datefmt="[%d-%b-%y %H:%M:%S]"
)

class StartDiagnosticTestAgent(ScAgentClassic):
    def __init__(self):
        super().__init__("action_start_diagnostic_test")

    
    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("StartDiagnosticTestAgent finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result
    

    def run(self, action: ScAddr) -> ScResult:
        self.logger.info("StartDiagnosticTestAgent started")

        # rrel_1 -> (action -> user);;
        [user] = get_action_arguments(action, 1)
        
        test = self.search_test()
        create_action("action_start_test", user, test)

        self.logger.info("StartDiagnosticTestAgent: finished successfully")
        return ScResult.OK
    
    def search_test(self):
        templ = ScTemplate()
        templ.triple(
            ScKeynodes.resolve("concept_test", sc_type.VAR_NODE_CLASS),
            sc_type.VAR_PERM_POS_ARC,
            (sc_type.VAR_NODE, "test")
        )
        search_results = search_by_template(templ)
        search_result = choice(search_results)
        return search_result.get("test")
