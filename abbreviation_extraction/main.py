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
# processin the document 
doc = nlp('Council of Europe 59 ("CoE") is the court ultimately responsible for applying European Convention on Human Rights 1972 (ECHR\' 72) and therefore it should apply to the Human Rights Act 1998 (HRA 98) ')

# for testing purposes, see the results returned from the abbreviation detector - TODO: remove 
print("Abbreviation", "\t", "Definition")
for abrv in doc._.abbreviations:
	print(f"{abrv} \t ({abrv.start}, {abrv.end}) {abrv._.long_form}")
    