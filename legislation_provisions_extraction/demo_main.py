from legislation_provisions import main 
import os
from bs4 import BeautifulSoup
import sys
sys.path.append("./")
from replacer import second_stage_replacer

def demo_main(): 
    enriched_judgment_file_path = "legislation_provisions_extraction/test_judgments"
    file_list = [i for i in os.listdir(enriched_judgment_file_path) if i.endswith('.xml')]

    for filename in file_list:
        resolved_refs = main(enriched_judgment_file_path, filename)
        if resolved_refs:
            enriched_judgment_file = os.path.join(enriched_judgment_file_path, filename)
            with open(enriched_judgment_file, "r") as f:
                soup = BeautifulSoup(f, 'xml')
            enriched_file = second_stage_replacer.oblique_replacement(soup, resolved_refs)

            output_file = f"legislation_provisions_extraction/output/{filename}".replace(".xml", "_enriched.xml")

            with open(output_file, "w") as data_out:
                data_out.write(enriched_file)

demo_main()

