from sc_kpm import ScKeynodes
from sc_client.models import ScAddr, ScTemplate
from sc_client.constants import sc_type
from sc_client.client import search_by_template


def get_user_passing_test_history(user: ScAddr, test: ScAddr) -> ScAddr:
    # nrel_user_passing_test_history -> ((user => test) => user_passing_test_history);;
    templ = ScTemplate()
    # nrel_user_passing_test_history -> ((=>) => user_passing_test_history)
    templ.quintuple(
        (sc_type.VAR_COMMON_ARC, "_common_arc"),                #        =>
        sc_type.VAR_COMMON_ARC,                                 #        || 
                                                                #        \/
        (sc_type.VAR_NODE, "_user_passing_test_history"),       # user_passing_test_history
        sc_type.VAR_PERM_POS_ARC,                               #                <-
        ScKeynodes.resolve("nrel_user_passing_test_history", sc_type.CONST_NODE_NON_ROLE)
    )
    # (user => test)
    templ.triple(
        user,
        "_common_arc", # => 
        test
    )
    search_results = search_by_template(templ)
        
    if search_results:
        search_result = search_results[0]
        return search_result.get("_user_passing_test_history")
    
    return ScAddr()

def is_question_answer_correct(question_answer: ScAddr, question: ScAddr) -> bool:
    templ = ScTemplate()
    templ.quintuple(
        question,
        sc_type.VAR_COMMON_ARC,
        question_answer,
        sc_type.VAR_PERM_POS_ARC,
        ScKeynodes.resolve("nrel_correct_answer", sc_type.CONST_NODE_NON_ROLE)
    )

    search_results = search_by_template(templ)
    
    if search_results:
        return True
        
    return False