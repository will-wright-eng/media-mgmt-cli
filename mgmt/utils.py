from typing import List

from typer import echo


def check_selection(selection: int, option_list: List[int]):
    try:
        if option_list and selection in option_list:
            return True
        else:
            echo("Invalid selection. Aborting")
            return False
    except TypeError as e:
        raise e
    return


def get_restore_status_short(restore_status: str) -> str:
    if not restore_status:
        status = "None"
    elif "ongoing-request" in restore_status and "true" in restore_status:
        status = "incomplete"
    elif "ongoing-request" in restore_status and "false" in restore_status:
        status = "complete"
    else:
        status = "unknown"
    return status
