from typing import Optional

import lxml.etree

namespaces = {
    None: "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
    "uk": "https://caselaw.nationalarchives.gov.uk/akn",
}


def expand_namespace(namespaced_name: str) -> str:
    if ":" not in namespaced_name:
        return namespaced_name
    namespace, _, name = namespaced_name.partition(":")
    return f"{{{namespaces[namespace]}}}{name}"


def create_tag(
    tag: str, contents: str = "", attrs: Optional[dict[str, str]] = None
) -> lxml.etree._Element:
    """Create a tag with text-based contents, parsed correctly as XML"""
    """Note that this will create bloated XML in the enrichment process, but that Marklogic will canonicalise the XML when it is ingested"""
    if not attrs:
        attrs = {}
    root_start = '<root xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">'
    root_end = "</root>"
    xml = root_start + contents + root_end
    root = lxml.etree.fromstring(xml)
    root.tag = tag
    for attr, value in attrs.items():
        root.attrib[expand_namespace(attr)] = value
    return root


def create_tag_string(tag: str, contents: str = "", attrs: Optional[dict[str, str]] = None) -> str:
    return lxml.etree.tostring(create_tag(tag=tag, contents=contents, attrs=attrs)).decode("utf-8")
