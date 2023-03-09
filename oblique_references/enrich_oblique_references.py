"""Module containing the function that enriches oblique references"""

import re

from oblique_references.oblique_references import oblique_pipeline
from replacer.second_stage_replacer import oblique_replacement


def enrich_oblique_references(file_content: str) -> str:
    """Determines oblique references in the file_content and then returns
    an enriched file content with the replacements applied

    Args:
        file_content (str): original file content

    Returns:
        (str): updated file content with enriched oblique references
    """
    # split file_content into header and judgment to ensure replacements only occur in judgment body
    judgment_split = re.split("(</header>)", file_content)

    resolved_refs = oblique_pipeline(judgment_split[2])

    if not resolved_refs:
        return []

    output_file_data = oblique_replacement(judgment_split[2], resolved_refs)
    # combine header with replaced text content before uploading to enriched bucket
    judgment_split[2] = output_file_data

    return "".join(judgment_split)
