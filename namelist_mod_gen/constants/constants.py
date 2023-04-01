import datetime
import os

SRC_ROOT_DIR = os.path.dirname(os.path.abspath(__file__)).replace('constants', '')
temp = SRC_ROOT_DIR.split('/')[0:-2]
PROJECT_DIR = os.path.join('/', *temp)
DB_PATH = os.path.join(PROJECT_DIR, 'db', 'translations.db')
LOG_DIR = f"{PROJECT_DIR}/logs/{datetime.datetime.now().strftime('%d.%m.%Y_%H.%M.%S')}.main.log"
TEMPLATES_DIR = os.path.join(SRC_ROOT_DIR, 'templates')
NAMELIST_TEMPLATE = 'namelist.txt'
NAMELIST_DEF_TEMPLATE = 'descriptors.yml'
NAMELIST_LOC_TEMPLATE = 'localisation.yml'

SUB_TOKENS = {
    "C": "SEQ",
    "O": "ORD",
    "R": "R",
    "ORD": "ORD",
    "(ONL)": "(ONL)"
}

ORD_EXAMPLES = {
    "$C$": "1",
    "$O$": "First",
    "$R$": "IV",
    "$ORD$": "First"
}
LANGUAGES = {
    'pt': 'braz_por',
    'fr': 'french',
    'de': 'german',
    'pl': 'polish',
    'ru': 'russian',
    'es': 'spanish',
    'zh': 'simp_chinese',
    'ja': 'japanese',
    'ko': 'korean'
}

TABLE_LANGUAGES = {
    'portuguese',
    'french',
    'german',
    'polish',
    'russian',
    'spanish',
    'chinese',
    'japanese',
    'korean'
}

ARGOS_LANGUAGES = [
    'Portuguese',
    'French',
    'German',
    'Polish',
    'Russian',
    'Spanish',
    'Chinese',
    'Japanese',
    'Korean'
]

LANG_TRANS_MAP = {
    'en': ["alibaba", "baidu", "caiyun", "google", "iciba", "iflytek", "itranslate", "lingvanex",
           "niutrans", "papago", "reverso", "sogou", "tencent", "translateCom", "yandex", "youdao"],
    'pt': ["google", "niutrans", "reverso", "tencent", "translateCom"],
    'fr': ["alibaba", "caiyun", "google", "iflytek", "niutrans", "reverso", "tencent", "translateCom"],
    'de': ["google", "iflytek", "niutrans", "reverso", "sogou", "tencent", "translateCom"],
    'pl': ["google", "iflytek", "niutrans", "reverso", "translateCom"],
    'ru': ["alibaba", "caiyun", "google", "iflytek", "niutrans", "papago", "reverso", "sogou", "tencent",
           "translateCom", "youdao"],
    'es': ["alibaba", "caiyun", "google", "iflytek", "itranslate", "niutrans", "reverso", "sogou", "tencent",
           "translateCom", "youdao"],
    'zh-CN': ["alibaba", "caiyun", "google", "iflytek", "niutrans", "reverso", "sogou", "tencent", "translateCom",
              "youdao"],
    'ja': ["google", "iflytek", "itranslate", "niutrans", "papago", "reverso", "sogou", "translateCom"],
    'ko': ["baidu", "google", "iciba", "iflytek", "itranslate", "papago", "reverso", "sogou", "translateCom", "youdao"]
}

NOTITLE_FIELDS = [
    'namelist_title', 'namelist_author', 'namelist_id'
]

NO_TRANSLATE_FIELD_FRAGMENTS = [
    '_author', '_id', '_army', 'an_machine', 'fn_fleet'
]

UNKEYED_FIELDS = ['namelist_id', 'id', 'namelist_author', 'namelist_title']

TIER_MAP = {
    'sn_tier_x': ['sn_flagship', 'sn_juggernaut', 'sn_colossus'],
    'sn_tier_a': ['sn_battleship', 'sn_carrier', 'sn_dreadnought'],
    'sn_tier_b': ['sn_cruiser', 'sn_strike_cruiser', 'sn_battle_cruiser'],
    'sn_tier_c': ['sn_corvette', 'sn_frigate', 'sn_destroyer'],
    'sn_col': ['sn_colonizer', 'sn_sponsored_colonizer'],
    'sn_con': ['sn_constructor'],
    'sn_tran': ['sn_transport'],
    'sn_sci': ['sn_science', 'sn_exploration_ship']
}

DL_CODES = {
    'pt': 'PT-BR',
    'zh-CN': 'ZH'
}
# Increasing this above this number risks encountering deadlock
THREAD_CONCURRENCY = 50

OPUS_UNSUPPORTED = ['ja', 'pt', 'pl', 'zh-CN', 'ko']
