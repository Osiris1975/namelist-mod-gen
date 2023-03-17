import os 

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(ROOT_DIR, 'templates')
DEFAULT_AUTHOR = "Anonymous"
DEFAULT_MOD_NAME = "Example Mod"
NAMELIST_TEMPLATE = 'namelist.txt'
LOCALIZATION_TEMPLATE = 'name_lists_loc.yml'
ORD_NAMES_LOC_TEMPLATE = 'ord_names_loc.yml'
MOD_OUTPUT_DIR = os.path.join(ROOT_DIR, 'generated_mods')

ORD_TYPES = {
    "C": "SEQ",
    "O": "ORD",
    "R": "R",
    "ORD": "ORD",
    "HEX": "HEX",
    "CC": "SEQ",
    "CCC": "SEQ"
}

# SEQUENTIAL_NAMES = [
#  OSIRIS_DEVTEST_MACHINEASSAULT1:0 "$ORD$ an_machine_assault_1"
#  OSIRIS_DEVTEST_MACHINEASSAULT2:0 "$ORD$ an_machine_assault_2"
#  OSIRIS_DEVTEST_MACHINEASSAULT3:0 "$ORD$ an_machine_assault_3"
#  OSIRIS_DEVTEST_MACHINEDEFENSE:0 "$ORD$ an_machine_defense"
#  OSIRIS_DEVTEST_OCCUPATIONARMY:0 "$ORD$ an_occupation_army"
#  OSIRIS_DEVTEST_POSTATOMICARMY:0 "$ORD$ an_postatomic_army"
#  OSIRIS_DEVTEST_PRIMITIVEARMY:0 "$ORD$ an_primitive_army"
#  OSIRIS_DEVTEST_PSIONICARMY:0 "$ORD$ an_psionic_army"
#  OSIRIS_DEVTEST_ROBOTICARMY:0 "$ORD$ an_robotic_army"
#  OSIRIS_DEVTEST_ROBOTICDEFENSEARMY:0 "$ORD$ an_robotic_defense_army"
#  OSIRIS_DEVTEST_ROBOTICOCCUPATIONARMY:0 "$ORD$ an_robotic_occupation_army"
#  OSIRIS_DEVTEST_SLAVEARMY:0 "$ORD$ an_slave_army"
#  OSIRIS_DEVTEST_UNDEADARMY:0 "$ORD$ an_undead_army"
#  OSIRIS_DEVTEST_XENOMORPHARMY:0 "$ORD$ an_xenomorph_army"
#  OSIRIS_DEVTEST_FLEETNAMES:0 "$ORD$ Fleet"
# ]
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
