import io
import logging
import os
import traceback

from multiprocess.pool import ThreadPool
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
                'overwrite': name_lists['overwrite'],
            }
    :return:
    """
    nl_output_path = os.path.join(name_list['directories']['common'], f"{name_list['id']}.txt")

    if name_list['overwrite']:
        try:
            log.warning(f'Overwrite selected for {name_list["title"]}. Removing {nl_output_path}')
            os.remove(nl_output_path)
        except FileNotFoundError as e:
            log.error(f'Error occurred while deleting file {nl_output_path}: {e}')
            log.debug(traceback.format_exc())

    render_dict = {k: " ".join(v) for k, v, in name_list['data'].items()}
    for k, v in render_dict.items():
        if 'second_names' in k and len(v) == 0:
            render_dict[k] = '\"\"'

    with io.open(nl_output_path, 'w', encoding='utf-8-sig') as file:
        name_list = name_list['namelist_template'].render(render_dict)
        file.write(name_list)
        log.info(f'Namelist file written to {nl_output_path}')


def generate(func, name_lists, parallel_process):
    """
    A generic/partial function for executing functions with a common input and processing flow.
    :param func: The function to execute inside generate
    :param name_lists: the namelist master dictionary
    :param parallel_process: boolean indicating if parallel processing should be used
    :return:
    """
    try:
        if 'namelists' not in name_lists:
            log.error('Input dictionary does not contain "namelists" key')
        inputs_name_lists = []
        for namelist_id, namelist_data in name_lists['namelists'].items():
            name_list = {
                'id': namelist_id,
                'data': namelist_data['data'],
                'directories': name_lists['directories'],
                'title': ''.join(namelist_data['data']['namelist_title']),
                'namelist_template': name_lists['namelist_template'],
                'localisation_template': name_lists['localisation_template'],
                'overwrite': name_lists['overwrite'],
            }
            inputs_name_lists.append(name_list)

        if parallel_process:
            with ThreadPool() as pool:
                pool.map(func, inputs_name_lists)
        else:
            for name_list in inputs_name_lists:
                func(name_list)
    except Exception as e:
        log.error(f"Error writing namelist file: {e}")
        log.debug(traceback.format_exc())