import datetime
import os

# Path constants
SRC_ROOT_DIR = os.path.dirname(os.path.abspath(__file__)).replace('constants', '')
temp = SRC_ROOT_DIR.split('/')[0:-2]
PROJECT_DIR = os.path.join('/', *temp)
LOG_DIR = f"{PROJECT_DIR}/logs/{datetime.date.today().strftime('%d.%m.%Y')}.main.log"
TEMPLATES_DIR = os.path.join(SRC_ROOT_DIR, 'templates')
NAMELIST_TEMPLATE = 'namelist.txt'
NAMELIST_DEF_TEMPLATE = 'descriptors.yml'
NAMELIST_LOC_TEMPLATE = 'localisation.yml'

# Ratelimiting constants
RL_CALLS = 100
RL_PERIOD = 1

# DB Constants
# DB_PATH = os.path.join(PROJECT_DIR, 'db', 'translations_new.db')
DB_PATH = 'postgresql+psycopg2://nmg@localhost:5432/translations'
DB_POOL_TIMEOUT = 600
DB_MAX_OVERFLOW = 12
DB_POOL_SIZE = 64

# Text & Language Constants

OPUS_UNSUPPORTED = ['ja', 'pt', 'pl', 'zh-CN', 'ko']

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
    'en': 'english',
    'pt': 'portuguese',
    'fr': 'french',
    'de': 'german',
    'pl': 'polish',
    'ru': 'russian',
    'es': 'spanish',
    'zh': 'chinese',
    'ja': 'japanese',
    'ko': 'korean'
}

TABLE_LANGUAGES = {
    'portuguese': 'pt',
    'french': 'fr',
    'german': 'de',
    'polish': 'pl',
    'russian': 'ru',
    'spanish': 'es',
    'chinese': 'zh',
    'japanese': 'ja',
    'korean': 'ko'
}

PARADOX_LANGUAGES = {
    'portuguese': 'braz_por',
    'chinese': 'simp_chinese',
    'french': 'french',
    'german': 'german',
    'polish': 'polish',
    'russian': 'russian',
    'spanish': 'spanish',
    'japanese': 'japanese',
    'korean': 'korean',
    'english': 'english'
}

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

NAMELIST_CATEGORY_TAGS = {
    '_AN_': 'army',
    '_CN_': 'character',
    '_FN_': 'fleet',
    '_PN_': 'planet',
    '_SN_': 'ship'
}
NOTITLE_FIELDS = [
    'namelist_title', 'namelist_author', 'namelist_id'
]

NO_TRANSLATE_FIELDS = [
    'namelist_author', 'namelist_id',
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

