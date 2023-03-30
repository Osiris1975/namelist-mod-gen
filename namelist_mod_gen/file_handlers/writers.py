import io
import logging
import os
import traceback

log = logging.getLogger('NMG')


def write_template(source_data, dest_file, template, lang):
    with io.open(dest_file, 'w', encoding='utf-8-sig') as file:
        if lang:
            nl_loc = template.render(dict_item=source_data, lang=lang)
        else:
            nl_loc = template.render(dict_item=source_data)
        file.write(nl_loc)
        log.info(f'Namelist localisation file written to {dest_file}')


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

    if name_list['overwrite']:
        try:
            log.warning(f'Overwrite selected for {name_list["title"]}. Removing {dest_file}')
            os.remove(dest_file)
        except FileNotFoundError as e:
            log.error(f'Error occurred while deleting file {dest_file}: {e}')
            log.debug(traceback.format_exc())
    else:
        if os.path.exists(dest_file):
            log.warning(f'Overwrite not selected for {name_list["title"]}. Skipping writing of {dest_file}')
            return

    render_dict = {k: " ".join(v) for k, v, in name_list['data'].items()}
    for k, v in render_dict.items():
        if 'second_names' in k and len(v) == 0:
            render_dict[k] = '\"\"'

    write_template(render_dict, dest_file, name_list['namelist_template'], None)
    with io.open(dest_file, 'w', encoding='utf-8-sig') as file:
        name_list = name_list['namelist_template'].render(render_dict)
        file.write(name_list)
        log.info(f'Namelist file written to {dest_file}')
