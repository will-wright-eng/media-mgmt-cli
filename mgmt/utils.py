from typing import List

from typer import echo


def echo_dict(input_dict: dict) -> None:
    """
    Prints a dictionary with its keys and values

    Args:
        input_dict (dict): The dictionary to be printed.
    """
    for key, val in input_dict.items():
        echo(f"{key[:18]+'..' if len(key)>17 else key}{(20-int(len(key)))*'.'}{val}")


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
