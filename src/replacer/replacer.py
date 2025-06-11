"""
Replacer logic for first phase enrichment.
Handles the replacements of abbreviations, legislation, and case law.
"""

import json

from utils.custom_types import Replacement


def encode_replacements_to_string(replacement_list: list[Replacement]) -> str:
    """
    Writes tuples from a list
    :param replacement_list:
    :return: tuple json file
    """
    tuple_file = ""
    for i in replacement_list:
        replacement_object = {f"{type(i).__name__}": list(i)}
        tuple_file += json.dumps(replacement_object)
        tuple_file += "\n"

    return tuple_file
