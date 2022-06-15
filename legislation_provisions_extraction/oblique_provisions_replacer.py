def replace_provisions(file_data, replacement, section_found, section_number): 
    canonical = replacement['canonical'] + " s. " + section_number 
    href = replacement['href']
    replacement_string = f'<ref uk:type="legislation" uk:canonical="{canonical}" href="{href}">{section_found}</ref>'
    file_data = str(file_data).replace(section_found, replacement_string)
    return file_data