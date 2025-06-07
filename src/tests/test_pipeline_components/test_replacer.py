"""Tests the replacer.replacer module's `encode_replacements_to_string` function"""

import json
import unittest
from collections import namedtuple

from replacer.replacer import encode_replacements_to_string


class TestWriteReplacementsFile(unittest.TestCase):
    """
    Tests `encode_replacements_to_string` function
    """

    def test_encode_replacements_to_string(self):
        """
        Given a list of named tuples
        When `encode_replacements_to_string` is called with them
        Then a string is returned in a jsonl structure
            with each line a dict for each named tuple
            where they key is the name of the namedtuple and
            the value is list corresponding to all the values in the named tuple
        """
        foo = namedtuple("foo", "a b c d e")
        bar = namedtuple("bar", "f g h")

        replacements = [
            foo(
                a="[2020] EWHC 537 (Ch)",
                b="[2020] EWHC 537 (Ch)",
                c="2020",
                d="https://caselaw.nationalarchives.gov.uk/ewhc/ch/2020/537",
                e=True,
            ),
            bar(
                f="[2022] 1 P&CR 123",
                g="[2022] 1 P&CR 123",
                h="2022",
            ),
        ]

        replacements_string = encode_replacements_to_string(replacements)

        replacements_list = replacements_string.splitlines()

        expected_key_value_pairs = [
            {
                "foo": [
                    "[2020] EWHC 537 (Ch)",
                    "[2020] EWHC 537 (Ch)",
                    "2020",
                    "https://caselaw.nationalarchives.gov.uk/ewhc/ch/2020/537",
                    True,
                ],
            },
            {"bar": ["[2022] 1 P&CR 123", "[2022] 1 P&CR 123", "2022"]},
        ]

        for index, replacement in enumerate(replacements_list):
            replacement_dict = json.loads(replacement)
            expected_key_value_pair = expected_key_value_pairs[index]
            assert expected_key_value_pair == replacement_dict


if __name__ == "__main__":
    unittest.main()
