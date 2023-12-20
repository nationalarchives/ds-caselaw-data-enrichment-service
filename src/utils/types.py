from typing import NewType

Replacement = NewType("Replacement", tuple[str, str, str, str, bool])
# ('[2022] UKSC 3', '[2022] UKSC 3', '2022', 'https://caselaw.nationalarchives.gov.uk/uksc/2022/3', True)

Reference = list[tuple[tuple[int, int], str]]
# The first part is a span (from inter-character-position to another) and the second is the string found there


# from typing import TypeAlias
# Replacement: TypeAlias = Iterable
