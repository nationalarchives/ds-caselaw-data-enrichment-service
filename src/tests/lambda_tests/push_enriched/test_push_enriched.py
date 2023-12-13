import os

import pytest


@pytest.fixture(scope="module", autouse=True)
def set_env():
    os.environ["SOURCE_BUCKET"] = "1"
    os.environ["API_PASSWORD"] = "1"
    os.environ["API_USERNAME"] = "1"
    os.environ["ENVIRONMENT"] = "1"


def test_fcl_uri():
    # currently we need to set the environment variables before we import the module.
    from lambdas.push_enriched_xml.index import fcl_uri

    assert fcl_uri("ewhc-ch-2023-1") == "ewhc/ch/2023/1"
    assert fcl_uri("ewhc-ch-2023-1-press-summary-1") == "ewhc/ch/2023/1/press-summary/1"
