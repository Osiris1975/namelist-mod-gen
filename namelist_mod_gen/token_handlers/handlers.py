import logging

import regex

from clean.cleaner import clean_input_text

log = logging.getLogger('NMG')


def retokenize(text_dict):
    """
    Append or prepend texts that have Stellaris sequence tokens to the translated text.
    :param text_dict: A text dict containing original_txt, detokenized_txt, token, loc(the position the token should be
    placed in(0=None, 1=prepend, 2=append), and the translation of the original_txt.
    :return: text_dict with retokenized translation
    """
    if text_dict['loc'] == 2:
        final_txt = ' '.join([text_dict['translation'], text_dict['token']])
    elif text_dict['loc'] == 1:
        final_txt = ' '.join([text_dict['token'], text_dict['translation']])
    else:
        final_txt = text_dict['translation']
    return final_txt


def detokenize(text):
    """
    Given a text, this checks for stellaris sequence tokens and moves them to their own key:value pair in the text_dict
    so they won't be passed on to the translation functions.
    :param text: A text destined to be translated.
    :return: a dictionary with a detokenized version of the original text added to it as well as additional meta info
    for use by downstream processing.
    """
    try:
        detokenized_txt = regex.sub(r'\$\w+\$', '', text)
        response = {
            'original_txt': text,
            'detokenized_txt': clean_input_text(detokenized_txt).title(),
            'token': '',
            'loc': 0
        }
        token = regex.search(r'^\$\w+\$', text)
        if token:
            response['token'] = token.group()
            response['loc'] = 1
        token = regex.search(r'\$\w+\$$', text)
        if token:
            response['token'] = token.group()
            response['loc'] = 2
        token = regex.search(r'\(\w+\)', text)
        if token:
            response['token'] = token.group()
            response['detokenized_txt'] = text.replace(response['token'], '').title()
            response['loc'] = 2
        return response
    except Exception as e:
        log.error(f'Token matching failed: {e}')
