import os 

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(ROOT_DIR, 'templates')
NAMELIST_TEMPLATE = 'namelist.txt'
LOCALIZATION_TEMPLATE = 'name_lists_loc.yml'
ORD_NAMES_LOC_TEMPLATE = 'ord_names_loc.yml'
MOD_OUTPUT_DIR = os.path.join(ROOT_DIR, 'generated_mods')

ORD_TYPES = {
    "C": "SEQ",
    "O": "ORD",
    "R": "R",
    "ORD": "ORD"
}