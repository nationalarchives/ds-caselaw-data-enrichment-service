import lxml.etree

from utils.custom_types import XMLFragmentAsString


def xml_escape(text: str) -> str:
    """Safely escape XML special characters"""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&amp;lt;")
        .replace(">", "&amp;gt;")
        .replace('"', "&amp;quot;")
        .replace("'", "&amp;apos;")
    )


namespaces = {
    None: "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
    "uk": "https://caselaw.nationalarchives.gov.uk/akn",
}

XSLT_TEMPLATE = """
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
  xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
    <xsl:output method="xml" indent="yes"/>

    <xsl:template match="xml">
        <xsl:copy>
            <xsl:apply-templates select="text()"/>
        </xsl:copy>
    </xsl:template>

    <xsl:template match="text()[contains(., '{replaced_string}')]">
        <xsl:value-of select="substring-before(., '{replaced_string}')"/>
        {replacement_tag}
        <xsl:value-of select="substring-after(., '{replaced_string}')"/>
    </xsl:template>

    <!-- Copy everything else as-is -->
    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>
</xsl:stylesheet>
"""


def replace_string_with_tag(xml: XMLFragmentAsString, string: str, tag: str) -> XMLFragmentAsString:
    """
    Replace citations in running text, but not in XML attributes
    This is probably quite inefficient, being called once per replacement! But we can make it better later
    """
    # Add root tags to the XML, with uk namespace if not already present
    uk_ns_1 = 'xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn"'
    uk_ns_2 = "xmlns:uk='https://caselaw.nationalarchives.gov.uk/akn'"
    needs_wrapper = uk_ns_1 not in str(xml) and uk_ns_2 not in str(xml)
    root_start = f"<root {uk_ns_1}>" if needs_wrapper else "<root>"
    root_end = "</root>"
    xml_wrapped = XMLFragmentAsString(root_start + str(xml) + root_end)
    root = lxml.etree.fromstring(xml_wrapped)

    # DRAGON: this currently isn't working but stops it crashing
    sanitised_string = xml_escape(string)

    stylesheet = lxml.etree.XML(XSLT_TEMPLATE.format(replaced_string=sanitised_string, replacement_tag=tag))
    transformer = lxml.etree.XSLT(stylesheet)
    output = lxml.etree.tostring(transformer(root))
    decoded_output = output.decode("utf-8")

    # Remove the root tags that were added at the start of the function
    final_output = decoded_output[len(root_start) : -len(root_end)]
    return XMLFragmentAsString(final_output)


def expand_namespace(namespaced_name: str) -> str:
    if ":" not in namespaced_name:
        return namespaced_name
    namespace, _, name = namespaced_name.partition(":")
    return f"{{{namespaces[namespace]}}}{name}"


def create_tag(tag: str, contents: str = "", attrs: dict[str, str] | None = None) -> lxml.etree._Element:
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


def create_tag_string(tag: str, contents: str = "", attrs: dict[str, str] | None = None) -> XMLFragmentAsString:
    return XMLFragmentAsString(lxml.etree.tostring(create_tag(tag=tag, contents=contents, attrs=attrs)).decode("utf-8"))
