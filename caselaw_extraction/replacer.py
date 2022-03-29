import re

def replacer_caselaw(file_data, replacement):
  # TODO: href attribute to TNA URI
  # add a new field in manifest for URI --> check URI material
  """
  String replacement in the XML
  :param file_data: XML file
  :param replacement: tuple of citation match and corrected citation
  :return: enriched XML file data
  """
  replacement_string = f'<ref type="case" isNeutral="{str(replacement[3]).lower()}" canonical="{replacement[1]}" year="{replacement[2]}">{replacement[0]}</ref>'
  file_data = str(file_data).replace(replacement[0], replacement_string)
  # file_data = re.sub(re.escape(replacement[0]), replacement_string, str(file_data))
  return file_data

def replacer_leg(file_data, replacement):
  # TODO: href attribute to TNA URI
  # add a new field in manifest for URI --> check URI material
  """
  String replacement in the XML
  :param file_data: XML file
  :param replacement: tuple of citation match and corrected citation
  :return: enriched XML file data
  """
  replacement_string = f'<ref type="legislation" href="{replacement[1]}">{replacement[0]}</ref>'
  # file_data = str(file_data).replace(replacement[0], replacement_string)
  file_data = re.sub(replacement[0], replacement_string, str(file_data))
  return file_data

def replacer_abbr(file_data, replacement):
  # TODO: href attribute to TNA URI
  # add a new field in manifest for URI --> check URI material
  """
  String replacement in the XML
  :param file_data: XML file
  :param replacement: tuple of citation match and corrected citation
  :return: enriched XML file data
  """
  replacement_string = f'<ref type="abbreviation" longform="{replacement[1]}">{replacement[0]}</ref>'
  file_data = str(file_data).replace(str(replacement[0]), replacement_string)
  # file_data = re.sub(str(replacement[0]), replacement_string, str(file_data))
  return file_data