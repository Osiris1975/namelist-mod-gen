import io
import logging
import os
import traceback

from multiprocess.pool import ThreadPool
log = logging.getLogger('NMG')


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
