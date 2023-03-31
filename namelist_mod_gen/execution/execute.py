import logging
import traceback

from multiprocess.pool import ThreadPool

log = logging.getLogger('NMG')


def executor(func, namelists, parallel_process):
    """
    A generic/partial function for executing functions with a common input and processing flow.
    :param func: The function to execute inside generate
    :param namelists: the namelist master dictionary
    :param parallel_process: boolean indicating if parallel processing should be used
    :return:
    """
    try:
        if 'namelists' not in namelists:
            log.error('Input dictionary does not contain "namelists" key')
        inputs_name_lists = []
        for namelist_id, namelist_data in namelists['namelists'].items():
            namelist = {
                'id': namelist_id,
                'data': namelist_data['data'],
                'directories': namelists['directories'],
                'title': ''.join(namelist_data['data']['namelist_title']),
                'template': namelists['template'],
                'overwrite': namelists['overwrite'],
                'namelists': namelists['namelists']
            }
            if 'author' in namelists.keys():
                namelist['author'] = namelists['author']
            inputs_name_lists.append(namelist)

        if parallel_process:
            with ThreadPool() as pool:
                pool.map(func, inputs_name_lists)
        else:
            for namelist in inputs_name_lists:
                func(namelist)
    except Exception as e:
        log.error(f"Error writing namelist file: {e}")
        log.debug(traceback.format_exc())
