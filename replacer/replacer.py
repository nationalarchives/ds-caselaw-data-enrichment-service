import re
import json

"""
Replacer logic for the entire enrichment pipeline. 
Handles the replacements of abbreviations, legislation, and case law. 
"""


def replacer_caselaw(file_data, replacement):
  # TODO: href attribute to TNA URI
  # add a new field in manifest for URI --> check URI material
  """
  String replacement in the XML
  :param file_data: XML file
  :param replacement: tuple of citation match and corrected citation
  :return: enriched XML file data
  """
  replacement_string = f'<ref uk:type="case" href="{replacement[3]}" uk:isNeutral="{str(replacement[4]).lower()}" uk:canonical="{replacement[1]}" uk:year="{replacement[2]}">{replacement[0]}</ref>'
  file_data = str(file_data).replace(replacement[0], replacement_string)
  return file_data

def replacer_leg(file_data, replacement):
  """
  String replacement in the XML
  :param file_data: XML file
  :param replacement: tuple of citation match and corrected citation
  :return: enriched XML file data
  """
  replacement_string = f'<ref uk:type="legislation" href="{replacement[1]}" uk:canonical="{replacement[2]}">{replacement[0]}</ref>'
  file_data = str(file_data).replace(replacement[0], replacement_string)
  return file_data

def replacer_abbr(file_data, replacement):
  """
  String replacement in the XML
  :param file_data: XML file
  :param replacement: tuple of citation match and corrected citation
  :return: enriched XML file data
  """
  replacement_string = f'<abbr title="{replacement[1]}">{replacement[0]}</abbr>'
  file_data = str(file_data).replace(str(replacement[0]), replacement_string)
  return file_data

def replacer_pipeline(file_data, REPLACEMENTS_CASELAW, REPLACEMENTS_LEG, REPLACEMENTS_ABBR):
  for replacement in list(set(REPLACEMENTS_CASELAW)):
    file_data = replacer_caselaw(file_data, replacement)

  for replacement in list(set(REPLACEMENTS_LEG)):
    print(replacement)
    file_data = replacer_leg(file_data, replacement)
  
  for replacement in list(set(REPLACEMENTS_ABBR)):
    file_data = replacer_abbr(file_data, replacement)

  return file_data

def write_replacements_file(replacement_list):
  tuple_file = ""
  for i in replacement_list:
    replacement_object = {"{}".format(type(i).__name__): list(i)}
    tuple_file += json.dumps(replacement_object)
    tuple_file += "\n"

  return tuple_file