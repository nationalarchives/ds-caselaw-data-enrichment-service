import datetime
import logging
import re
from io import BytesIO

import pandas as pd
from SPARQLWrapper import CSV, SPARQLWrapper

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

LEGISLATION_API_URL = "https://www.legislation.gov.uk/sparql"


def fetch_legislation(sparql_username: str, sparql_password: str, days: int | None) -> pd.DataFrame:
    """
    Fetch new legislation from legislation.gov.uk since the start day, if given,
    otherwise all legislation
    """
    today = datetime.datetime.today()
    start_date = today - datetime.timedelta(days) if days else None

    log_string = f"Retrieving all legislation from {LEGISLATION_API_URL}"
    log_string += " since {start_date}" if start_date else ""
    LOGGER.info(log_string)

    sparql = SPARQLWrapper(LEGISLATION_API_URL)
    sparql.setCredentials(user=sparql_username, passwd=sparql_password)
    sparql.setReturnFormat(CSV)

    filter_string = f'FILTER("{today}" >  str(?actTime) && str(?actTime) > "{start_date}")' if start_date else ""

    sparql.setQuery(
        f"""
                prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                prefix xsd: <http://www.w3.org/2001/XMLSchema#>
                prefix void: <http://rdfs.org/ns/void#>
                prefix dct: <http://purl.org/dc/terms/>
                prefix sd: <http://www.w3.org/ns/sparql-service-description#>
                prefix prov: <http://www.w3.org/ns/prov#>
                prefix leg: <http://www.legislation.gov.uk/def/legislation/>
                select distinct ?ref  ?title ?ref_version ?shorttitle ?citation ?acronymcitation ?year
                where {{
                   ?activity prov:endedAtTime ?actTime .
                   ?graph prov:wasInfluencedBy ?activity .
                   ?activity rdf:type <http://www.legislation.gov.uk/def/provenance/Addition> .
                   ?dataUnitDataSet sd:namedGraph ?graph .
                   <http://www.legislation.gov.uk/id/dataset/topic/core> void:subset ?dataUnitDataSet .
                   graph ?graph {{ ?ref a leg:Legislation; a leg:UnitedKingdomPublicGeneralAct ;
                                        leg:title ?title ;
                                        leg:interpretation ?version .
                                        OPTIONAL {{?ref leg:citation ?citation}} .
                                        OPTIONAL {{?ref leg:acronymCitation ?acronymcitation}} .
                                        OPTIONAL {{?ref leg:year ?year}} .
                                        OPTIONAL {{?ref_version   leg:shortTitle ?shorttitle}} .}}
                    {filter_string}
                }}
                """
    )

    results = sparql.query().convert()
    df = pd.read_csv(BytesIO(results))
    LOGGER.info("Legislation retrieved")

    df = _enhance_legislation_data(df)
    return df


def _enhance_legislation_data(df):
    stitles = ["shorttitle", "citation", "acronymcitation"]
    df["candidate_titles"] = df[stitles].apply(list, axis=1)
    df = df.explode("candidate_titles")
    df = df[~df["candidate_titles"].isna()].drop_duplicates("candidate_titles")
    df["for_fuzzy"] = df.candidate_titles.apply(lambda x: re.search(r"Act\s+(\d{4})", x) is not None)
    return df
