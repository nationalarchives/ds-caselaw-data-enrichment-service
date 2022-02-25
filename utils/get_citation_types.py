import pandas as pd 

MANIFEST = pd.read_csv("/Users/daniel.hoadley/Development/project_TNA/rules/2022_02_24_Citation_Manifest.csv")
citation_types = list(set(MANIFEST["citationType"].tolist()))
print (citation_types)