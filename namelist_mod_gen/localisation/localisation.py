import io
import logging

from jinja2 import Environment, FileSystemLoader

import constants.constants as c

logger = logging.getLogger('NMG')

template_loader = FileSystemLoader(searchpath=c.TEMPLATES_DIR)
template_env = Environment(loader=template_loader)


def localize_namelist(namelist):
    """
    :param namelist:
    :return:
    """
    print(namelist)
    quotified = {k: f'\"{v}\"' for k, v in namelist.items()}
    with io.open(ord_loc_file, 'w', encoding='utf-8-sig') as file:
        quotified = {k: f'\"{v}\"' for k, v in loc_dict.items()}
        namelist_loc_template = template_env.get_template(c.NL_LOC_TEMPLATE)
        nl_loc = namelist_loc_template.render(dict_item=quotified, lang=lang)
        file.write(nl_loc)
        logger.info(f'Namelist localisation file written to {ord_loc_file}')


def localize_namelists(namelists, localisation_dirs):
    """

    :param namelists:
    :param translate:
    :return:
    """
    inputs = []
    for ld in localisation_dirs:
        pass
    for nl in namelists:
        localize_namelist(nl)
