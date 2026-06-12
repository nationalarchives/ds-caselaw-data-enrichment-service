import psycopg2
from moto import mock_aws

from lambdas.enrichment_lambda.index import enrich_xml_file
from tests.postgres_test_factory import postgres_instance


def _create_lookup_table(pg_dsn: dict) -> None:
    conn = psycopg2.connect(
        host=pg_dsn["host"],
        port=pg_dsn["port"],
        dbname=pg_dsn["database"],
        user=pg_dsn["user"],
        password="",
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE ukpga_lookup (
                    candidate_titles TEXT,
                    year INTEGER,
                    for_fuzzy BOOLEAN,
                    ref TEXT,
                    citation TEXT
                )
                """,
            )
            cursor.execute(
                """
                INSERT INTO ukpga_lookup (candidate_titles, year, for_fuzzy, ref, citation)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    "Children and Families Act 2014",
                    2014,
                    False,
                    "https://www.legislation.gov.uk/ukpga/2014/6",
                    "Children and Families Act 2014",
                ),
            )
        conn.commit()
    finally:
        conn.close()


def test_enrich_xml_file_end_to_end_without_unittest_mock(monkeypatch):
    with postgres_instance() as pg:
        pg_dsn = pg.dsn()
        _create_lookup_table(pg_dsn)

        with mock_aws():
            import boto3

            region = "eu-west-2"
            rules_bucket = "integration-rules-bucket"
            rules_key = "rules/citation_patterns.jsonl"
            lookup_name = "integration-db-lookup"

            s3 = boto3.client("s3", region_name=region)
            s3.create_bucket(
                Bucket=rules_bucket,
                CreateBucketConfiguration={"LocationConstraint": region},
            )
            # Keep caselaw patterns empty in this E2E to focus the assertion on full pipeline execution.
            s3.put_object(Bucket=rules_bucket, Key=rules_key, Body="")

            secrets = boto3.client("secretsmanager", region_name=region)
            secrets.create_secret(Name=lookup_name, SecretString="integration-test-password")

            monkeypatch.setenv("RULES_FILE_BUCKET", rules_bucket)
            monkeypatch.setenv("RULES_FILE_KEY", rules_key)
            monkeypatch.setenv("DATABASE_NAME", pg_dsn["database"])
            monkeypatch.setenv("DATABASE_USERNAME", pg_dsn["user"])
            monkeypatch.setenv("DATABASE_HOSTNAME", pg_dsn["host"])
            monkeypatch.setenv("DATABASE_PORT", str(pg_dsn["port"]))
            monkeypatch.setenv("SECRET_PASSWORD_LOOKUP", lookup_name)
            monkeypatch.setenv("REGION_NAME", region)

            original_xml = """<?xml version='1.0' encoding='UTF-8'?>
<akomaNtoso xmlns='http://docs.oasis-open.org/legaldocml/ns/akn/3.0' xmlns:uk='https://caselaw.nationalarchives.gov.uk/akn'>
    <judgment>
        <header>
            <p>Header content only.</p>
        </header>
        <judgmentBody>
            <p>This judgment body includes enough textual context to exercise the full enrichment pipeline in a realistic way, including tokenisation, paragraph scanning, replacement generation, and XML serialisation. The Children and Families Act 2014 applies in this context and is referred to explicitly for enrichment validation. Additional narrative text is included so that abbreviation chunking has sufficient document length to operate without short-document boundary artefacts.</p>
        </judgmentBody>
    </judgment>
</akomaNtoso>
"""

            enriched_xml = enrich_xml_file(original_xml)

            assert "Children and Families Act 2014" in enriched_xml
            assert "https://www.legislation.gov.uk/ukpga/2014/6" in enriched_xml
            assert "<ref" in enriched_xml
            assert "<judgmentBody>" in enriched_xml
