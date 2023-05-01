import regex
from namelist_mod_gen.file_handlers.csv import _get_template_variables


def read_namelist_txt(namelist_file):
    with open(namelist_file, 'r') as f:
        contents = f.read()

    namelist_dict = dict()
    namelist_fields = _get_template_variables()
    for field in namelist_fields:
        uncategorized_field = "_".join(field.split("_")[1:])
        pattern_suffix = r"\s*=\s*{\s*([^}]+)\s*}"
        pattern_string = f"{uncategorized_field}{pattern_suffix}"
        pattern = regex.compile(pattern_string)

        match = pattern.search(contents)
        namelist_dict[field] = match
        print(field)
