""" Handles the database connection """


import pandas as pd
import psycopg2


def create_connection(db, user, password, host, port):
    """
    Connect to the PostgreSQL database server
    :param db
    :param user
    :param password
    :param host
    :param port
    :return: db connection
    """
    conn = None
    try:
        # connect to the PostgreSQL server
        print("Connecting to the PostgreSQL database...")
        conn = psycopg2.connect(
            database=db, user=user, password=password, host=host, port=port
        )
        return conn
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        raise
    # return conn


def get_manifest_row(conn, rule_id):
    """
    Select all fields/rows from manifest that match the rule id
    :param conn: database connection created with create_connection()
    :param rule_id: ID of manifest rule to be extracted
    :return: DataFrame of matched rule
    """
    matched_rule = pd.read_sql(
        "SELECT * FROM manifest where id='{0}'".format(rule_id), conn
    )
    return matched_rule


def get_matched_rule(conn, rule_id):
    """
    Uses database connection to select fields/rows of interest from manifest that match the rule id
    :param conn: database connection, required
    :param rule_id: rule_id string, required
    :return: variables family, URItemplate, is_neutral, is_canonical, citation_type, canonical_form
    """
    matched_rule = get_manifest_row(conn, rule_id)
    family = matched_rule["family"].iloc[0].lower()
    URItemplate = matched_rule["uri_template"].iloc[0]
    is_neutral = bool(matched_rule["is_neutral"].iloc[0])
    is_canonical = matched_rule["is_canonical"].iloc[0]
    citation_type = matched_rule["citation_type"].iloc[0]
    canonical_form = matched_rule["canonical_form"].iloc[0]
    return family, URItemplate, is_neutral, is_canonical, citation_type, canonical_form


def get_legtitles(conn):
    """
    Retrieves legislation titles from legislation lookup table
    :param conn: database connection, required
    :return: DataFrame of legislation titles
    """
    leg_titles = pd.read_sql(
        "SELECT candidate_titles, year, for_fuzzy FROM ukpga_lookup", conn
    )
    return leg_titles


# sql queries for legislation lookup table
href_query = """SELECT ref FROM ukpga_lookup WHERE candidate_titles= %(title)s"""
canonical_query = (
    """SELECT citation FROM ukpga_lookup WHERE candidate_titles= %(title)s"""
)


def get_hrefs(conn, title):
    """
    Retrieves link to legislation title
    :param conn: database connection, required
    :param title: legislation title, required
    :return: link to legislation title
    """
    test = pd.read_sql_query(href_query, conn, params={"title": "{}".format(title)})
    return test.ref.values[0]


def get_canonical_leg(conn, title):
    """
    Retrieves canonical form of legislation title
    :param conn: database connection, required
    :param title: legislation title, required
    :return: canoncial form of legislation title
    """
    canonical_leg = pd.read_sql(
        canonical_query, conn, params={"title": "{}".format(title)}
    )
    return canonical_leg.citation.values[0]


def close_connection(conn):
    """
    Closes the Database connection
    :param conn: database connection to be closed
    """
    conn.close()
