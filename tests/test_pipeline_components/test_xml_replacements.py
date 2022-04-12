import unittest
import sys
sys.path.append("./")
from replacer.replacer import replacer_caselaw, replacer_leg, replacer_abbr, replacer_pipeline
import json

"""
    Testing the xml replacements at each stage of the pipeline, to validate that they have been replaced correctly. 

    The replacements are being made based off of tuples saved in files at each of the stage. 
"""

# create mock function for the db connection - extracting the logic from main.py
def mock_replace_data(file_data):
    # convert the file to a list 
    replacements = []
    tuple_file = open("./tests/test_pipeline_components/verified_test_files/tuples.jsonl", "r")
    for line in tuple_file:
        replacements.append(json.loads(line))

    replacement_tuples_case = mock_replacement_tuple(replacements, 'case')
    file_data_enriched = replacer_pipeline(file_data, replacement_tuples_case, [], [])
    output_file = f"./tests/test_pipeline_components/output_test_files/case_law_replaced".replace(".xml", "_enriched.xml")
    mock_write_file(output_file, file_data_enriched)

    replacement_tuples_leg = mock_replacement_tuple(replacements, 'leg')
    file_data_enriched = replacer_pipeline(file_data, replacement_tuples_case, replacement_tuples_leg, [])
    output_file = f"./tests/test_pipeline_components/output_test_files/case_law_legislation_replaced".replace(".xml", "_enriched.xml")
    mock_write_file(output_file, file_data_enriched)

    replacement_tuples_abb = mock_replacement_tuple(replacements, 'abb')
    file_data_enriched = replacer_pipeline(file_data, replacement_tuples_case, replacement_tuples_leg, replacement_tuples_abb)
    output_file = f"./tests/test_pipeline_components/output_test_files/case_law_legislation_abbreviations_replaced".replace(".xml", "_enriched.xml")
    mock_write_file(output_file, file_data_enriched)



def mock_write_file(file_path, file_data_enriched): 
    with open(file_path, "w") as data_out:
        data_out.write(file_data_enriched)

def mock_replacement_tuple(replacements, key_str): 
    tuple_list = []
    for i in replacements:
        key, value = list(i.items())[0]
        if key == key_str:
            new_tuple = tuple(i[key_str])
            tuple_list.append(new_tuple)

    return tuple_list


class TestXMLFiles(unittest.TestCase): 
    def test_case_law(self): 
        with open("./tests/test_pipeline_components/verified_test_files/test_judgment.xml", "r", encoding="utf-8") as file_in:
            file_data = file_in.read()
            mock_replace_data(file_data)
    
if __name__ == '__main__':
    unittest.main()
