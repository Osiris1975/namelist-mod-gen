import os 

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(ROOT_DIR, 'templates')
NAMELIST_TEMPLATE = 'namelist.txt'
LOCALIZATION_TEMPLATE = 'localization.yml'
MIL_NAMES_LOC_TEMPLATE = 'military_names_loc.yml'
MOD_OUTPUT_DIR = os.path.join(ROOT_DIR, 'generated_mods')
NAME_LIST_OUTPUT_DIR = os.path.join(ROOT_DIR, 'common', 'name_lists')
LOCALIZATION_OUTPUT_DIR = os.path.join(ROOT_DIR, 'localisation', 'english')