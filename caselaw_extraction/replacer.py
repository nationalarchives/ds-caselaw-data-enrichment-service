def replacer(file_data, replacement):
  # TODO: href attribute to TNA URI
  # add a new field in manifest for URI --> check URI material
  """
  String replacement in the XML
  :param file_data: XML file
  :param replacement: tuple of citation match and corrected citation
  :return: enriched XML file data
  """
  replacement_string = f'<ref type="case" year="{replacement[2]}" canonical_form="{replacement[1]}">{replacement[0]}</ref>'
  file_data = str(file_data).replace(replacement[0], replacement_string)
  return file_data