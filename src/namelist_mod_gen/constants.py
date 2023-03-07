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

LANGUAGES = {
    'en': 'english',
    'pt': 'braz_por',
    'fr': 'french',
    'de': 'german',
    'pl': 'polish',
    'ru': 'russian',
    'es': 'spanish',
    'zh-Hans': 'simp_chinese',
    'ja': 'japanese',
    'ko': 'korean'
}

NOTITLE_FIELDS = [
    'namelist_title', 'namelist_author', 'namelist_id'
]

NO_TRANSLATE_FIELD_FRAGMENTS = [
    '_author', '_id', '_army', 'an_machine', 'fn_fleet'
]

CHUNK_SIZE = 4000