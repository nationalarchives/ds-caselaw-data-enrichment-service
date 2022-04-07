import re
import json

def replacer_caselaw(file_data, replacement):
  # TODO: href attribute to TNA URI
  # add a new field in manifest for URI --> check URI material
  """
  String replacement in the XML
  :param file_data: XML file
  :param replacement: tuple of citation match and corrected citation
  :return: enriched XML file data
  """
  replacement_string = f'<ref type="case" href="{replacement[3]}" isNeutral="{str(replacement[4]).lower()}" canonical="{replacement[1]}" year="{replacement[2]}">{replacement[0]}</ref>'
  file_data = str(file_data).replace(replacement[0], replacement_string)
  return file_data

def replacer_leg(file_data, replacement):
  """
  String replacement in the XML
  :param file_data: XML file
  :param replacement: tuple of citation match and corrected citation
  :return: enriched XML file data
  """
  replacement_string = f'<ref type="legislation" href="{replacement[1]}">{replacement[0]}</ref>'
  file_data = str(file_data).replace(replacement[0], replacement_string)
  # file_data = re.sub(replacement[0], replacement_string, str(file_data))
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

def write_repl_file(tuple_file, replacement_list):
  for i in replacement_list:
    replacement_object = {"{}".format(type(i).__name__): list(i)}
    json.dump(replacement_object, tuple_file)
    tuple_file.write("\n")