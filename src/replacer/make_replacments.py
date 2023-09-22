import re
from typing import List


def split_text_by_closing_header_tag(file_content: str) -> List[str]:
    """
    Split file_content into start, closing header tag and body
    to ensure replacements only occur in the body.
    """
    header_patterns = [r"</header>", r"<header/>"]
    for pattern in header_patterns:
        if pattern in file_content:
            return re.split(f"({pattern})", file_content)
    return ["", "", file_content]
