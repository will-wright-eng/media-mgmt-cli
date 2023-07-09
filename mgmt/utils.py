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
