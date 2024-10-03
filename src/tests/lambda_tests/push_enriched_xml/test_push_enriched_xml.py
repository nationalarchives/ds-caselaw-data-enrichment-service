# from lambdas.push_enriched_xml.index import (  # noqa: E402
#     process_event,
# )
from unittest.mock import patch

from lambdas.push_enriched_xml.index import (  # noqa: E402
    process_event,
)


class FakeSQSRecord(dict):
    def __init__(self):
        self.body = '{"Validated": true}'
        self["messageAttributes"] = {
            "source_key": {"stringValue": "uksc/2024/1/press-summary/1"},
            "source_bucket": {"stringValue": ""},
        }
        self["Validated"] = None


@patch("lambdas.push_enriched_xml.index.boto3")
@patch("lambdas.push_enriched_xml.index.requests")
def test_patch_url_has_press_summary_with_a_hyphen(requests, boto3):
    process_event(FakeSQSRecord())
    assert (
        requests.patch.call_args_list[0][0][0]
        == "https://api.caselaw.nationalarchives.gov.uk/judgment/uksc/2024/1/press-summary/1"
    )
