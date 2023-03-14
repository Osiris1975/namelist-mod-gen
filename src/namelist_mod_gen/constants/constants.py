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
    # 'fr': 'french',
    # 'de': 'german',
    # 'pl': 'polish',
    # 'ru': 'russian',
    # 'es': 'spanish',
    # 'zh-CN': 'simp_chinese',
    # 'ja': 'japanese',
    # 'ko': 'korean'
}

LANG_TRANS_MAP = {
    'en': ["alibaba", "baidu", "bing", "caiyun", "deepl", "google", "iciba", "iflytek", "itranslate", "lingvanex",
           "niutrans", "papago", "reverso", "sogou", "tencent", "translateCom", "yandex", "youdao"],
    'pt': ["bing", "deepl", "google", "niutrans", "papago", "reverso", "tencent", "translateCom"],
    'fr': ["alibaba", "baidu", "bing", "caiyun", "deepl", "google", "iciba", "iflytek", "itranslate", "lingvanex",
           "niutrans", "papago", "reverso", "sogou", "tencent", "translateCom", "yandex", "youdao"],
    'de': ["baidu", "bing", "deepl", "google", "iciba", "iflytek", "itranslate", "lingvanex",
           "niutrans", "papago", "reverso", "sogou", "tencent", "translateCom", "yandex", "youdao"],
    'pl': ["baidu", "bing", "deepl", "google", "iciba", "iflytek", "itranslate",
           "niutrans", "papago", "reverso", "translateCom", "yandex"],
    'ru': ["alibaba", "baidu", "bing", "caiyun", "deepl", "google", "iciba", "iflytek", "itranslate", "lingvanex",
           "niutrans", "papago", "reverso", "sogou", "tencent", "translateCom", "yandex", "youdao"],
    'es': ["alibaba", "baidu", "bing", "caiyun", "deepl", "google", "iciba", "iflytek", "itranslate", "lingvanex",
           "niutrans", "papago", "reverso", "sogou", "tencent", "translateCom", "yandex", "youdao"],
    'zh-CN': ["alibaba", "baidu", "bing", "caiyun", "deepl", "google", "iciba", "iflytek", "itranslate", "lingvanex",
              "niutrans", "papago", "reverso", "sogou", "tencent", "translateCom", "yandex",
              "youdao"],
    'ja': ["baidu", "bing", "caiyun", "deepl", "google", "iciba", "iflytek", "itranslate", "lingvanex",
           "niutrans", "papago", "reverso", "sogou", "tencent", "translateCom", "yandex", "youdao"],
    'ko': ["baidu", "bing", "deepl", "google", "iciba", "iflytek", "itranslate",
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