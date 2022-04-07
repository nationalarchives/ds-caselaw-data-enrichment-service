import bs4 as BeautifulSoup
import pandas as pd

def load_patterns(conn):
  """
  Write patterns file
  :param conn: Database connection
  """
  rules_manifest = pd.read_sql('''SELECT * FROM manifest''', conn)
  patterns = rules_manifest["pattern"].tolist()
  with open("rules/citation_patterns.jsonl", "w+") as patterns_file:
    for pattern in patterns:
        patterns_file.write(pattern + "\n")

def parse_file(file_data):
  soup = BeautifulSoup.BeautifulSoup(str(file_data), "lxml")
  judgment_content = soup.find_all("content")
  judgment_content_text = " ".join([content.text.strip() for content in judgment_content])
  return judgment_content_text