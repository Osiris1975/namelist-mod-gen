import itertools
import regex

control_chars = ''.join(map(chr, itertools.chain(range(0x00, 0x20), range(0x7f, 0xa0), [0xFEFF, 0x200b])))
re = regex.compile('[%s]' % regex.escape(control_chars))


def clean_input_text(txt):
    return re.sub('', txt).strip()
