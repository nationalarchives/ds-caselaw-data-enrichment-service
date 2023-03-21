"""Module contains integration tests for enrich_oblique_references"""

import unittest
from pathlib import Path

from oblique_references.enrich_oblique_references import (
    enrich_oblique_references,
)

FIXTURE_DIR = Path(__file__).parent.parent.resolve() / "fixtures/"


class TestEnrichObliqueReferences(unittest.TestCase):
    """Integration tests for enrich_oblique_references"""

    def test_enrich_oblique_references(self):
        """
        Given xml judgment content without enriched oblique references
        When it is passed to `enrich_oblique_references`
        Then xml judgment content is returned with enriched oblique references
        """
        input_file_path = f"{FIXTURE_DIR}/ewhc-ch-2023-257_enriched_stage_1.xml"
        with open(input_file_path, "r", encoding="utf-8") as input_file:
            input_file_content = input_file.read()

        enriched_content = enrich_oblique_references(input_file_content)

        expected_file_path = f"{FIXTURE_DIR}/ewhc-ch-2023-257_enriched_stage_2.xml"
        with open(expected_file_path, "r", encoding="utf-8") as expected_file:
            expected_enriched_content = expected_file.read()

        assert enriched_content.strip() == expected_enriched_content.strip()


if __name__ == "__main__":
    unittest.main()
