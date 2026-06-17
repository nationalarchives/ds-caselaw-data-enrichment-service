# src/tests/conftest.py

import pandas as pd
import pytest
from spacy.lang.en import English
from sqlalchemy import create_engine
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgres_container():
    container = PostgresContainer("postgres:17")
    container.start()
    yield container
    container.stop()


@pytest.fixture(scope="session")
def db_engine(postgres_container):
    return create_engine(postgres_container.get_connection_url())


# IMPORTANT: this gives transaction isolation per test


@pytest.fixture(autouse=True)
def clean_db(db_engine):
    with db_engine.begin() as conn:
        conn.exec_driver_sql("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")


@pytest.fixture
def db_connection(db_engine):
    with db_engine.connect() as conn:
        yield conn


FIXTURE_DIR = "src/caselaw_extraction/rules"


@pytest.fixture
def manifest_table(db_engine):
    df = pd.read_csv(FIXTURE_DIR + "/2022_06_30_Citation_Manifest.csv")
    df.to_sql("manifest", db_engine, if_exists="append", index=False)
    return "manifest"


@pytest.fixture(scope="session")
def nlp():
    nlp = English()
    nlp.max_length = 1_500_000
    nlp.add_pipe("entity_ruler").from_disk(FIXTURE_DIR + "/citation_patterns.jsonl")
    return nlp


@pytest.fixture()
def seed_ukpga_lookup(db_engine):
    sql = """
    CREATE TABLE IF NOT EXISTS ukpga_lookup (
        candidate_titles VARCHAR(100) NOT NULL,
        ref VARCHAR(100) NOT NULL,
        citation VARCHAR(100) NOT NULL,
        year BIGINT NOT NULL,
        for_fuzzy BOOLEAN NOT NULL
    );

    INSERT INTO ukpga_lookup (candidate_titles, ref, citation, year, for_fuzzy)
    VALUES
        ('Adoption and Children Act 2002',
         'http://www.legislation.gov.uk/ukpga/2002/38',
         'citation_abc',
         2002,
         true),
        ('def', 'ref_def', 'citation_def', 2001, true),
        ('ghi', 'ref_ghi', 'citation_ghi', 2002, false)
    ON CONFLICT DO NOTHING;
    """

    with db_engine.begin() as conn:
        conn.exec_driver_sql(sql)
