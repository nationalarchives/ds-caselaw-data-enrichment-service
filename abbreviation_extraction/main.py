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
doc = nlp('Paragraph 5 of Sally’s skeleton argument refers to the fact that she had paid a substantial sum which “was inclusive of an occupation rent for the entirety of the period from the death of Roger Kingsley 30 September 2018”; and paragraph 6 complains about an error in the claimants’ draft order: “Paragraph 5 contains an error in that the use and occupation of the Properties is that of the First, not the Second Defendant.” (Sally’s emphasis)')

# for testing purposes, see the results returned from the abbreviation detector - TODO: remove 
print("Abbreviation", "\t", "Definition")
for abrv in doc._.abbreviations:
	print(f"{abrv} \t ({abrv.start}, {abrv.end}) {abrv._.long_form}")
    
