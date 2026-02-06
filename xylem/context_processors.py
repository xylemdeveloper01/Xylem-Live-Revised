from xylem.custom_messages.constants import CUSTOM_LEVELS, CUSTOM_MESSAGE_DISSMISSABLE_LEVELS_LIST, CUSTOM_MESSAGE_POPUP_LEVELS_LIST
from xylem_apps.a000_xylem_master import serve

def custom_vars(request):
    """
    Return a lazy 'messages' context variable as well as
    'CUSTOM_MESSAGE_LEVELS'.
    """
    return {
        "CUSTOM_MESSAGE_DISSMISSABLE_LEVELS_LIST": CUSTOM_MESSAGE_DISSMISSABLE_LEVELS_LIST,
        "CUSTOM_MESSAGE_POPUP_LEVELS_LIST": CUSTOM_MESSAGE_POPUP_LEVELS_LIST,
        "CUSTOM_MESSAGE_LEVELS": CUSTOM_LEVELS,
        "XYLEM_CODE": serve.xylem_code,
        "MALE": serve.Genders.Male,
        "YES_OPTION": serve.Others.yes_option,
        "NO_OPTION": serve.Others.no_option,
        "FIRST_PRODUCT_CATEGORY": serve.get_first_product_category(),
        "FIRST_TOOL_TYPE": serve.get_first_tool_type(),
        "FIRST_CHECKSHEET_STATUS": serve.get_checksheets_first_status_type(),
        "FIRST_WORKFLOW_STATUS": serve.get_worflows_first_status_type(),
        "FIRST_PAGINATION_OPTION": serve.get_first_pagination_option(),
        "FIRST_PN_DRAWING_STATUS" : serve.get_first_pn_drawing_status_option()
    }
