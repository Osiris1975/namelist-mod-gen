import os

SRC_ROOT_DIR = os.path.dirname(os.path.abspath(__file__)).replace('constants', '')
temp = SRC_ROOT_DIR.split('/')[0:-3]
PROJECT_DIR = os.path.join('/', *temp)
TEMPLATES_DIR = os.path.join(SRC_ROOT_DIR, 'templates')
NAMELIST_TEMPLATE = 'namelist.txt'
NL_DEF_TEMPLATE = 'definitions.yml'
NL_LOC_TEMPLATE = 'translations.yml'
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

LANG_TRANS_MAP = {
    'en': ["alibaba", "baidu", "caiyun", "google", "iciba", "iflytek", "itranslate", "lingvanex",
           "niutrans", "papago", "reverso", "sogou", "tencent", "translateCom", "yandex", "youdao"],
    'pt': ["google", "niutrans", "papago", "reverso", "tencent", "translateCom"],
    'fr': ["alibaba", "baidu", "caiyun", "google", "iciba", "iflytek", "itranslate",
           "niutrans", "papago", "reverso", "tencent", "translateCom", "yandex"],
    'de': ["baidu", "google", "iciba", "iflytek", "itranslate", "lingvanex",
           "niutrans", "papago", "reverso", "sogou", "tencent", "translateCom", "yandex", "youdao"],
    'pl': ["baidu", "google", "iciba", "iflytek", "itranslate",
           "niutrans", "papago", "reverso", "translateCom", "yandex"],
    'ru': ["alibaba", "baidu", "caiyun", "google", "iciba", "iflytek", "itranslate", "lingvanex",
           "niutrans", "papago", "reverso", "sogou", "tencent", "translateCom", "yandex", "youdao"],
    'es': ["alibaba", "baidu", "caiyun", "google", "iciba", "iflytek", "itranslate", "lingvanex",
           "niutrans", "papago", "reverso", "sogou", "tencent", "translateCom", "yandex", "youdao"],
    'zh-CN': ["alibaba", "baidu", "caiyun", "google", "iciba", "iflytek", "itranslate", "lingvanex",
              "niutrans", "papago", "reverso", "sogou", "tencent", "translateCom", "yandex",
              "youdao"],
    'ja': ["baidu", "google", "iciba", "iflytek", "itranslate", "niutrans", "papago", "reverso", "sogou", "translateCom", "yandex"],
    'ko': ["baidu", "google", "iciba", "iflytek", "itranslate",
           "papago", "reverso", "sogou", "translateCom", "yandex", "youdao"]
}

NOTITLE_FIELDS = [
    'namelist_title', 'namelist_author', 'namelist_id'
]

NO_TRANSLATE_FIELD_FRAGMENTS = [
    '_author', '_id', '_army', 'an_machine', 'fn_fleet'
]

UNKEYED_FIELDS = ['namelist_id', 'id', 'namelist_author', 'namelist_title']

THREAD_CONCURRENCY = 10

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
