import pandas as pd
import sqlite3
from sqlite3 import Error

def create_connection(db_file):
    """ 
    Create a database connection to the SQLite database specified by db_file
    :param db_file: Path to database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn

def get_manifest_row(conn, rule_id):
  """
  Select all fields/rows from manifest that match the rule id
  :param conn: database connection created with create_connection(db_file)
  :param rule_id: ID of manifest rule to be extracted
  :return: DataFrame of matched rule
  """
  matched_rule = pd.read_sql('''SELECT * FROM manifest WHERE id="{0}"'''.format(rule_id), conn)
  return matched_rule

def get_matched_rule(conn, rule_id):
  """
  Uses database connection to select matched rule row from manifest.
  :param conn: database connection, required
  :param rule_id: rule_id string, required
  :return: variables is_canonical, citation_type, canonical_form and rule_description for specified rule
  """
  matched_rule = get_manifest_row(conn, rule_id)
  is_canonical = matched_rule["isCanonical"].iloc[0]
  citation_type = matched_rule["citationType"].iloc[0]
  canonical_form = matched_rule["canonicalForm"].iloc[0]
  rule_description = matched_rule["description"].iloc[0]
  return is_canonical, citation_type, canonical_form, rule_description

def close_connection(conn):
  """
  Closes the Database connection
  :param conn: database connection to be closed
  """
  conn.close()