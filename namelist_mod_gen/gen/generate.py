import io
import logging
import os

from multiprocess.pool import ThreadPool
log = logging.getLogger('NMG')


def write_common_name_lists(name_lists, parallel_process=False):
    """
    Proxy function for writing the namelist common files iteratively or with multiprocessing.
    :param name_lists: a dictionary of name lists containing namelist_id, namelist_data, jinja2 templating object,
    destination directory for common namelist files, and overwrite directive.
    :param parallel_process: Boolean indicating whether to use multithreading for this step.
    :return:
    """
    inputs_name_lists = []
    for namelist_id, namelist_data in name_lists['namelists'].items():
        name_list = {
            'id': namelist_id,
            'data': namelist_data,
            'dest_dir': name_lists['directories']['common'],
            'title': ''.join(namelist_data['data']['namelist_title']),
            'template': name_lists['namelist_template'],
            'overwrite': name_lists['overwrite'],
        }
        inputs_name_lists.append(name_list)

    if parallel_process:
        with ThreadPool() as pool:
            pool.map(_write_common_namelist, inputs_name_lists)
    else:
        for name_list in inputs_name_lists:
            _write_common_namelist(name_list)


def _write_common_namelist(name_list):
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
    nl_output_path = os.path.join(name_list['dest_dir'], f"{name_list['id']}.txt")

    if name_list['overwrite']:
        try:
            log.warning(f'Overwrite selected for {name_list["title"]}. Removing {nl_output_path}')
            os.remove(nl_output_path)
        except FileNotFoundError:
            log.debug(f'File {nl_output_path} not found.')
    render_dict = {k: " ".join(v) for k, v, in name_list['data'].items()}
    for k, v in render_dict.items():
        if 'second_names' in k and len(v) == 0:
            render_dict[k] = '\"\"'

    with io.open(nl_output_path, 'w', encoding='utf-8-sig') as file:
        name_list = name_list['template'].render(render_dict)
        file.write(name_list)
        log.info(f'Namelist file written to {nl_output_path}')

