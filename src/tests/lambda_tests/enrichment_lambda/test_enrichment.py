from unittest.mock import patch

from lambdas.enrichment_lambda.enrich_xml import enrich_xml


class TestEnrichXmlFile:
    @patch("lambdas.enrichment_lambda.enrich_xml.add_timestamp_and_engine_version")
    @patch("lambdas.enrichment_lambda.enrich_xml.replace_legislation_provisions")
    @patch("lambdas.enrichment_lambda.enrich_xml.enrich_oblique_references")
    @patch("lambdas.enrichment_lambda.enrich_xml.make_post_header_replacements")
    @patch("lambdas.enrichment_lambda.enrich_xml.make_replacements_input")
    @patch("lambdas.enrichment_lambda.enrich_xml.determine_abbreviation_replacements")
    @patch("lambdas.enrichment_lambda.enrich_xml.determine_legislation_replacements")
    @patch("lambdas.enrichment_lambda.enrich_xml.determine_caselaw_replacements")
    @patch("lambdas.enrichment_lambda.enrich_xml.parse_file")
    def test_enrich_xml_file_orchestrates_pipeline(
        self,
        mock_parse,
        mock_caselaw,
        mock_legislation,
        mock_abbreviation,
        mock_make_replacements,
        mock_post_header,
        mock_oblique,
        mock_legislation_provisions,
        mock_timestamp,
    ):
        mock_parse.return_value = "<parsed/>"
        mock_caselaw.return_value = [{"caselaw": "ref"}]
        mock_legislation.return_value = [{"legislation": "ref"}]
        mock_abbreviation.return_value = [{"abbreviation": "ref"}]
        mock_make_replacements.return_value = '{"replacement": "json"}'
        mock_post_header.return_value = "<with_replacements/>"
        mock_oblique.return_value = "<with_oblique/>"
        mock_legislation_provisions.return_value = "<with_provisions/>"
        mock_timestamp.return_value = "<final_enriched/>"

        result = enrich_xml("<xml/>", [{"pattern": "test"}], "7.4.0")

        assert result == "<final_enriched/>"
        mock_parse.assert_called_once()
        mock_caselaw.assert_called_once()
        mock_legislation.assert_called_once()
        mock_abbreviation.assert_called_once()
        mock_timestamp.assert_called_once_with("<with_provisions/>", "7.4.0")

    @patch("lambdas.enrichment_lambda.enrich_xml.add_timestamp_and_engine_version")
    @patch("lambdas.enrichment_lambda.enrich_xml.replace_legislation_provisions")
    @patch("lambdas.enrichment_lambda.enrich_xml.enrich_oblique_references")
    @patch("lambdas.enrichment_lambda.enrich_xml.make_post_header_replacements")
    @patch("lambdas.enrichment_lambda.enrich_xml.make_replacements_input")
    @patch("lambdas.enrichment_lambda.enrich_xml.determine_abbreviation_replacements")
    @patch("lambdas.enrichment_lambda.enrich_xml.determine_legislation_replacements")
    @patch("lambdas.enrichment_lambda.enrich_xml.determine_caselaw_replacements")
    @patch("lambdas.enrichment_lambda.enrich_xml.parse_file")
    def test_enrich_xml_file_with_empty_pattern_list(
        self,
        mock_parse,
        mock_caselaw,
        mock_legislation,
        mock_abbreviation,
        mock_make_replacements,
        mock_post_header,
        mock_oblique,
        mock_legislation_provisions,
        mock_timestamp,
    ):
        mock_parse.return_value = "<parsed/>"
        mock_caselaw.return_value = []
        mock_legislation.return_value = []
        mock_abbreviation.return_value = []
        mock_make_replacements.return_value = "{}"
        mock_post_header.return_value = "<no_replacements/>"
        mock_oblique.return_value = "<no_oblique/>"
        mock_legislation_provisions.return_value = "<final/>"
        mock_timestamp.return_value = "<final_with_timestamp/>"

        result = enrich_xml("<xml/>", [], "7.4.0")

        assert result == "<final_with_timestamp/>"
