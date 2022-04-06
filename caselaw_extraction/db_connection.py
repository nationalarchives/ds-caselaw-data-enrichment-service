from numpy import mat
import pandas as pd
import psycopg2

def create_connection(db, user, host, port):
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(database=db, user=user, host=host, port=port)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    return conn

def get_manifest_row(conn, rule_id):
  """
  Select all fields/rows from manifest that match the rule id
  :param conn: database connection created with create_connection(db_file)
  :param rule_id: ID of manifest rule to be extracted
  :return: DataFrame of matched rule
  """
  matched_rule = pd.read_sql("SELECT * FROM manifest where id='{0}'".format(rule_id), conn)
  return matched_rule

def get_matched_rule(conn, rule_id):
  """
  Uses database connection to select matched rule row from manifest.
  :param conn: database connection, required
  :param rule_id: rule_id string, required
  :return: variables is_canonical, citation_type, canonical_form and rule_description for specified rule
  """
  matched_rule = get_manifest_row(conn, rule_id)
  family = matched_rule["family"].iloc[0].lower()
  URItemplate = matched_rule["URItemplate"].iloc[0]
  is_neutral = bool(matched_rule["isNeutral"].iloc[0])
  is_canonical = matched_rule["isCanonical"].iloc[0]
  citation_type = matched_rule["citationType"].iloc[0]
  canonical_form = matched_rule["canonicalForm"].iloc[0]
  return family, URItemplate, is_neutral, is_canonical, citation_type, canonical_form

def get_legtitles(conn):
  leg_titles = pd.read_sql('''SELECT candidate_titles, year, for_fuzzy FROM ukpga_lookup''', conn)
  return leg_titles

def get_hrefs(conn, title):
  ref_link = pd.read_sql("SELECT ref_version FROM ukpga_lookup WHERE candidate_titles='{0}'".format(title), conn)
  return ref_link.ref_version.values[0]

def close_connection(conn):
  """
  Closes the Database connection
  :param conn: database connection to be closed
  """
  conn.close()