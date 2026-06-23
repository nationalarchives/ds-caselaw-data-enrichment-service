# from pathlib import Path

# import boto3
# import freezegun
# import pandas as pd
# import pytest
# from lxml import etree
# from moto import mock_aws
# from sqlalchemy import URL, create_engine

# from lambdas.enrichment_lambda.index import enrich_xml


# def _repo_root() -> Path:
#     return Path(__file__).resolve().parents[4]


# def _canonicalize_xml(xml_text: str) -> str:
#     parser = etree.XMLParser(remove_blank_text=True)
#     root = etree.fromstring(xml_text.encode("utf-8"), parser)

#     # 1. Strip whitespace ONLY from text content and tail, preserving attributes
#     for elem in root.iter():
#         if elem.text and elem.text.strip():
#             # Normalize internal whitespace in text but keep single spaces
#             elem.text = " ".join(elem.text.split())
#         elif elem.text:
#             elem.text = None  # Remove purely whitespace text

#         if elem.tail and elem.tail.strip():
#             elem.tail = " ".join(elem.tail.split())
#         elif elem.tail:
#             elem.tail = None

#     # 2. Serialize
#     # C14N preserves structure; since we cleaned text/tail, output is clean
#     return etree.tostring(root, method="c14n", exclusive=False, with_comments=False).decode("utf-8")


# @pytest.mark.enable_socket
# @freezegun.freeze_time("2024-06-01 12:00:00")
# def test_original_to_enriched_output_matches_expected_xml(monkeypatch, db_engine):
#     root = _repo_root()
#     original_xml = (root / "test_files" / "ewca_civ_2025_673-original.xml").read_text()
#     expected_xml = (root / "test_files" / "ewca_civ_2025_673-enriched.xml").read_text()

#     pg_dsn = db_engine.url

#     region = "eu-west-2"
#     secret_name = "integration-db-lookup"  # noqa: S105
#     rules_bucket = "integration-rules-bucket"
#     rules_key = "rules/citation_patterns.jsonl"
#     monkeypatch.setenv("DATABASE_NAME", pg_dsn["database"])
#     monkeypatch.setenv("DATABASE_USERNAME", pg_dsn["user"])
#     monkeypatch.setenv("DATABASE_HOSTNAME", pg_dsn["host"])
#     monkeypatch.setenv("DATABASE_PORT", str(pg_dsn["port"]))
#     monkeypatch.setenv("DATABASE_PASSWORD", pg_dsn["password"])
#     monkeypatch.setenv("SPARQL_USERNAME", "enrichment-engine")
#     monkeypatch.setenv("SPARQL_PASSWORD", "popper-aorta-volumes-789")
#     monkeypatch.setenv("SECRET_PASSWORD_LOOKUP", secret_name)
#     monkeypatch.setenv("RULES_FILE_BUCKET", rules_bucket)
#     monkeypatch.setenv("RULES_FILE_KEY", rules_key)
#     monkeypatch.setenv("AWS_DEFAULT_REGION", region)

#     with mock_aws():
#         s3 = boto3.client("s3", region_name=region)
#         s3.create_bucket(
#             Bucket=rules_bucket,
#             CreateBucketConfiguration={"LocationConstraint": region},
#         )
#         patterns_path = root / "src" / "enrichment" / "caselaw_extraction" / "rules" / "citation_patterns.jsonl"
#         s3.put_object(Bucket=rules_bucket, Key=rules_key, Body=patterns_path.read_bytes())

#         secrets = boto3.client("secretsmanager", region_name=region)
#         secrets.create_secret(Name=secret_name, SecretString=pg_dsn["password"])

#         # update_legislation_table(trigger_date=None)
#         _seed_legislation(pg_dsn, root)  # still needed — no pipeline function populates this
#         _seed_manifest(pg_dsn, root)  # still needed — no pipeline function populates this

#         new_xml = enrich_xml(original_xml, enrichment_version="7.3.0")

#     new_xml_canonical = _canonicalize_xml(new_xml)
#     expected_xml_canonical = _canonicalize_xml(expected_xml)

#     with open("new_xml_canonical.xml", "w") as f:
#         f.write(new_xml_canonical)
#     with open("expected_xml_canonical.xml", "w") as f:
#         f.write(expected_xml_canonical)

#     assert new_xml_canonical == expected_xml_canonical, "Enriched XML does not match expected XML"


# def _seed_manifest(db_engine, root: Path) -> None:
#     manifest_csv = root / "src" / "enrichment" / "caselaw_extraction" / "rules" / "2022_06_30_Citation_Manifest.csv"
#     manifest_df = pd.read_csv(manifest_csv)
#     manifest_df.to_sql("manifest", db_engine, if_exists="replace", index=False)


# # currently, the legislation table is populated by the fetch_legislation function, but it only fetches a subset of the data. For testing, we need to seed the legislation table with a full dataset. This function reads a CSV dump of legislation data and populates the legislation table in the test database.
# # not sure if it is acceptable to store a CSV dump of legislation data in the repo yet
# # have done so locally by using the backfill_legislation function to fetch all legislation data and then exporting it to a CSV file.
# # Have not committed the CSV file to the repo yet, so this test will fail, until we do that,
# # or we allow this test to run backfill_legislation to populate the legislation table, which is slow and not ideal.
# def _seed_legislation(db_engine, root: Path) -> None:
#     legislation_csv = "dump.csv"
#     legislation_df = pd.read_csv(legislation_csv)
#     legislation_df.to_sql("ukpga_lookup", db_engine, if_exists="replace", index=False)
