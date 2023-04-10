import logging

import regex

from clean.cleaner import clean_input_text

log = logging.getLogger('NMG')


def retokenize(text):
    if text['loc'] == 2:
        final_txt = ' '.join([text['translation'], text['token']])
    elif text['loc'] == 1:
        final_txt = ' '.join([text['token'], text['translation']])
    else:
        final_txt = text['translation']
    return final_txt


def detokenize(txt):
    try:
        detokenized_txt = regex.sub(r'\$\w+\$', '', txt)
        response = {
            'original_txt': txt,
            'detokenized_txt': clean_input_text(detokenized_txt).title(),
            'token': '',
            'loc': 0
        }
        token = regex.search(r'^\$\w+\$', txt)
        if token:
            response['token'] = token.group()
            response['loc'] = 1
        token = regex.search(r'\$\w+\$$', txt)
        if token:
            response['token'] = token.group()
            response['loc'] = 2
        token = regex.search(r'\(\w+\)', txt)
        if token:
            response['token'] = token.group()
            response['detokenized_txt'] = txt.replace(response['token'], '').title()
            response['loc'] = 2
        return response
    except Exception as e:
        log.error(f'Token matching failed: {e}')
