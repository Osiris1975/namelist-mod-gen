import os
SRC_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(SRC_ROOT_DIR, 'templates')
NAMELIST_TEMPLATE = 'namelist.txt'
NL_TITLES_LOC_TEMPLATE = 'name_lists_loc.yml'
NAMELISTS_LOC_TEMPLATE = 'ord_names_loc.yml'
temp = SRC_ROOT_DIR.split('/')[0:-2]
temp.append('generated_mods')
MOD_OUTPUT_DIR = os.path.join('/', *temp)

ORD_TYPES = {
    "C": "SEQ",
    "O": "ORD",
    "R": "R",
    "ORD": "ORD"
}

ORD_EXAMPLES = {
    "$C$": "1",
    "$O$": "First",
    "$R$": "IV",
    "$ORD$": "First"
}
LANGUAGES = {
    'en': 'english',
    'pt': 'braz_por',
    'fr': 'french',
    'de': 'german',
    'pl': 'polish',
    'ru': 'russian',
    'es': 'spanish',
    'zh-CN': 'simp_chinese',
    'ja': 'japanese',
    'ko': 'korean'
}

NOTITLE_FIELDS = [
    'namelist_title', 'namelist_author', 'namelist_id'
]

NO_TRANSLATE_FIELD_FRAGMENTS = [
    '_author', '_id', '_army', 'an_machine', 'fn_fleet'
]

UNKEYED_FIELDS = ['namelist_id', 'id', 'namelist_author', 'namelist_title']

CHUNK_SIZE = 4000