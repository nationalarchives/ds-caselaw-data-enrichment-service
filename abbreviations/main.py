import spacy
from abbreviations import AbbreviationDetector
from spacy.language import Language

# TODO: figure out where this main abbreviations code will live 

nlp = spacy.load("en_core_web_sm")

# init the class - stateful pipeline component 
@Language.factory("abbreviation_detector")
def create_abbreviation_detector(nlp, name: str): 
	return AbbreviationDetector(nlp)

nlp.add_pipe("abbreviation_detector") 

# TODO: replace this to intake the different statements - this is where we'll integrate the pipeline
# processing the document 
doc = nlp('The European Court of Human Rights ("ECtHR 1959") is the court ultimately responsible for applying the European Convention on Human Rights ("ECHR") it should apply to Human Rights Act 1998 ("HRA 1998") ')

# for testing purposes, see the results returned from the abbreviation detector - TODO: remove 
print("Abbreviation", "\t", "Definition")
for abrv in doc._.abbreviations:
	print(f"{abrv} \t ({abrv.start}, {abrv.end}) {abrv._.long_form}")
    
