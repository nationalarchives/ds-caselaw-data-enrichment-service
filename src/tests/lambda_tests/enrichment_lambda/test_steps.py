from unittest.mock import Mock, patch

from lambdas.enrichment_lambda import steps


@patch("lambdas.enrichment_lambda.steps.provisions_pipeline", return_value=[])
def test_replace_legislation_provisions_returns_original_when_no_refs(_mock_pipeline):
    xml = "<akomaNtoso><judgment><p>No refs</p></judgment></akomaNtoso>"

    assert steps.replace_legislation_provisions(xml) == xml


@patch("lambdas.enrichment_lambda.steps.replace_references_by_paragraph")
@patch("lambdas.enrichment_lambda.steps.provisions_pipeline", return_value=[((1, 2), "ref")])
def test_replace_legislation_provisions_applies_replacements(_mock_pipeline, mock_replace):
    replaced = Mock()
    replaced.__str__ = Mock(return_value="<akomaNtoso><judgment><p>Updated</p></judgment></akomaNtoso>")
    mock_replace.return_value = replaced

    xml = "<akomaNtoso><judgment><p>Original</p></judgment></akomaNtoso>"

    result = steps.replace_legislation_provisions(xml)

    assert result == "<akomaNtoso><judgment><p>Updated</p></judgment></akomaNtoso>"
    assert mock_replace.call_count == 1
