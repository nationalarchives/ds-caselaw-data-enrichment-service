import lxml.etree

from lambdas.enrichment_lambda import steps


def _xml_is_valid(xml: str) -> bool:
    lxml.etree.fromstring(xml.encode("utf-8"))
    return True


def test_replace_legislation_provisions_no_refs_returns_valid_xml():
    xml_in = "<xml><judgmentBody><p>No legislation references.</p></judgmentBody></xml>"

    xml_output = steps.replace_legislation_provisions(xml_in)

    assert xml_output == xml_in
    assert _xml_is_valid(xml_output)


def test_replace_legislation_provisions_updates_xml_when_resolved_refs(monkeypatch):
    def fake_provisions_pipeline(_xml):
        return [((1, 2), "dummy-ref")]

    def fake_replace_references_by_paragraph(soup, _resolved_refs):
        soup.find("p").string = "Updated with provisions"
        return soup

    monkeypatch.setattr(steps, "provisions_pipeline", fake_provisions_pipeline)
    monkeypatch.setattr(steps, "replace_references_by_paragraph", fake_replace_references_by_paragraph)

    xml_in = "<xml><judgmentBody><p>Original text</p></judgmentBody></xml>"
    xml_output = steps.replace_legislation_provisions(xml_in)
    assert "Updated with provisions" in xml_output
    assert _xml_is_valid(xml_output)
