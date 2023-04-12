#!env/bin/python

import datetime
import logging
import re
from io import BytesIO

import pandas as pd
from SPARQLWrapper import CSV, SPARQLWrapper

from utils.environment_helpers import validate_env_variable
from utils.initialise_db import init_db_engine

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def get_leg_update(sparql_username, sparql_password, days=7):
    """
    Fetch new legislations from legislation.gov.uk every 7 days and update the table used
    during the legislation extraction pipeline
    """
    # date = pd.to_datetime(date)
    today = datetime.datetime.today()
    date = today - datetime.timedelta(days)

    sparql = SPARQLWrapper("https://www.legislation.gov.uk/sparql")
    sparql.setCredentials(user=sparql_username, passwd=sparql_password)
    sparql.setReturnFormat(CSV)
    df = pd.DataFrame()
    sparql.setQuery(
        """
                prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                prefix xsd: <http://www.w3.org/2001/XMLSchema#>
                prefix void: <http://rdfs.org/ns/void#>
                prefix dct: <http://purl.org/dc/terms/>
                prefix sd: <http://www.w3.org/ns/sparql-service-description#>
                prefix prov: <http://www.w3.org/ns/prov#>
                prefix leg: <http://www.legislation.gov.uk/def/legislation/>
                select distinct ?ref  ?title ?ref_version ?shorttitle ?citation ?acronymcitation ?year
                where {
                   ?activity prov:endedAtTime ?actTime .
                   ?graph prov:wasInfluencedBy ?activity .
                   ?activity rdf:type <http://www.legislation.gov.uk/def/provenance/Addition> .
                   ?dataUnitDataSet sd:namedGraph ?graph .
                   <http://www.legislation.gov.uk/id/dataset/topic/core> void:subset ?dataUnitDataSet .
                   graph ?graph { ?ref a leg:Legislation; a leg:UnitedKingdomPublicGeneralAct ;
                                        leg:title ?title ;
                                        leg:interpretation ?version .
                                        OPTIONAL {?ref leg:citation ?citation} .
                                        OPTIONAL {?ref leg:acronymCitation ?acronymcitation} .
                                        OPTIONAL {?ref leg:year ?year} .
                                        OPTIONAL {?ref_version   leg:shortTitle ?shorttitle} .}
                   FILTER(str(?actTime) > "%s")
                }
                """
        % date
    )
    results = sparql.query().convert()
    df = pd.read_csv(BytesIO(results))
    stitles = ["shorttitle", "citation", "acronymcitation"]
    df["candidate_titles"] = df[stitles].apply(list, axis=1)
    df = df.explode("candidate_titles")
    df = df[~df["candidate_titles"].isna()].drop_duplicates("candidate_titles")
    df["for_fuzzy"] = df.candidate_titles.apply(
        lambda x: re.search(r"Act\s+(\d{4})", x) != None
    )
    return df


def handler(event, context):
    """
    Function called by the lambda to update the legislation table
    """
    LOGGER.info("Lambda to update legislation database")

    sparql_username = validate_env_variable("SPARQL_USERNAME")
    sparql_password = validate_env_variable("SPARQL_PASSWORD")

    try:
        engine = init_db_engine()
        LOGGER.info("Engine created")

        print("Trigger Date: ", event["trigger_date"])

        if "trigger_date" in event:
            trigger_date = event["trigger_date"]
            if type(trigger_date) == int:
                df = get_leg_update(sparql_username, sparql_password, trigger_date)
                print(df)
                df.to_sql("ukpga_lookup", engine, if_exists="append", index=False)
            else:
                df = get_leg_update(sparql_username, sparql_password)
                print(df)
                df.to_sql("ukpga_lookup", engine, if_exists="append", index=False)

        engine.dispose()
        LOGGER.info("Legislation updated")

    except Exception as exception:
        LOGGER.error("Exception: %s", exception)
        raise
