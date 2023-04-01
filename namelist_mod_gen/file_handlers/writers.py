import io
import logging
import os
import traceback

log = logging.getLogger('NMG')


def write_common_namelist(name_list):
    """
    Converts a namelist dictionary to a namelist file.
    :param name_list: A dictionary containing the following:
                name_list = {
                'id': ID of the namelist,
                'data': A dictionary mapping the namelist keys and values,
                'dest_dir': the directory to write the namelist files to,
                'title': The title of the namelist,
                'template': jinja templating object,
                'overwrite': a bool indicating to overwrite existing files,
            }
    :return:
    """
    dest_file = os.path.join(name_list['directories']['common'], f"{name_list['id']}.txt")
    template = name_list['template']
    if name_list['overwrite']:
        try:
            log.warning(f'Overwrite selected for {name_list["title"]}. Removing {dest_file}')
            os.remove(dest_file)
        except FileNotFoundError as e:
            log.warning(f'Error occurred while deleting file {dest_file}: {e}')
            log.debug(traceback.format_exc())
    else:
        if os.path.exists(dest_file):
            log.warning(f'Overwrite not selected for {name_list["title"]}. Skipping writing of {dest_file}')
            return

    render_dict = {k: " ".join(v) for k, v, in name_list['data'].items()}
    for k, v in render_dict.items():
        if 'second_names' in k and len(v) == 0:
            render_dict[k] = '\"\"'

    write_template(
        dest_file=dest_file,
        render_dict=render_dict,
        template=template,
        encoding='utf-8-sig',
        lang=None
    )


def write_template(dest_file, render_dict, template, encoding, lang=None):
    with io.open(dest_file, 'w', encoding=encoding) as file:
        if lang:
            name_list = template.render(dict_item=render_dict, lang=lang)
        else:
            name_list = template.render(render_dict)
        file.write(name_list)
        log.info(f'Namelist file written to {dest_file}')