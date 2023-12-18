import lxml.etree


def canonical_xml(xml_bytes):
    """with thanks to https://stackoverflow.com/questions/52422385/python-3-xml-canonicalization"""
    val = (
        lxml.etree.tostring(lxml.etree.fromstring(xml_bytes), method="c14n2")
        .replace(b"\n", b"")
        .replace(b" ", b"")
    )
    return val


def assert_equal_xml(a, b):
    """Are the two inputs the same string when canonicalised? If not, display the first difference."""
    if isinstance(a, str):
        a = a.encode("utf-8")
    canon_a = canonical_xml(a)

    if isinstance(b, str):
        b = b.encode("utf-8")
    canon_b = canonical_xml(b)

    if canon_a != canon_b:
        for i, (char_a, char_b) in enumerate(zip(canon_a, canon_b)):
            if char_a != char_b:
                break
        width = 180
        raise AssertionError(
            f"xml mismatch at {i}\nbefore: {canon_a[i-width:i]}\n first: {canon_a[i:i+width]}\nsecond: {canon_b[i:i+width]}"
        )
