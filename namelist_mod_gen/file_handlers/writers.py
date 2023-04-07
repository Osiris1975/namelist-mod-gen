import io
import logging
import os
import traceback

log = logging.getLogger('NMG')


def write_common_namelist(namelist):
    """
    Converts a namelist dictionary to a namelist file.
    :param namelist: A dictionary containing the following:
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
    dest_file = os.path.join(namelist['directories']['common'], f"{namelist['id']}.txt")
    if not ok_to_overwrite(namelist, dest_file):
        return

    template = namelist['template']

    render_dict = {k: " ".join(v) for k, v, in namelist['data'].items()}
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


def ok_to_overwrite(namelist, dest_file):
    if namelist['overwrite']:
        try:
            log.warning(f'Overwrite selected for {namelist["title"]}. Removing {dest_file}')
            os.remove(dest_file)
            return True
        except FileNotFoundError as e:
            log.warning(f'Error occurred while deleting file {dest_file}: {e}')
            log.debug(traceback.format_exc())
    else:
        if os.path.exists(dest_file):
            log.warning(f'Overwrite not selected for {namelist["title"]}. Skipping writing of {dest_file}')
            return False
        else:
            return True
