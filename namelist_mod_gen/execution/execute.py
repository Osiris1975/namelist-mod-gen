import logging
import traceback

from multiprocess.pool import ThreadPool

log = logging.getLogger('NMG')


def executor(func, namelists_master):
    """
    A generic/partial function for executing functions with a common input and processing flow.
    :param func: The function to execute inside generate
    :param namelists_master: the namelist master dictionary
    :return:
    """
    log.info(f'Executor executing {func.__name__}')
    try:
        if 'namelists' not in namelists_master:
            log.error('Input dictionary does not contain "namelists" key')
        inputs_name_lists = []
        for namelist_id, namelist_data in namelists_master['namelists'].items():
            namelist = {
                'id': namelist_id,
                'data': namelist_data['data'],
                'directories': namelists_master['directories'],
                'title': ''.join(namelist_data['data']['namelist_title']),
                'template': namelists_master['template'],
                'overwrite': namelists_master['overwrite'],
                'translate': namelists_master['translate'],
                'namelists': namelists_master['namelists'],
            }
            if 'author' in namelists_master.keys():
                namelist['author'] = namelists_master['author']
            if 'available_apis' in namelists_master.keys():
                namelist['available_apis'] = namelists_master['available_apis']
            inputs_name_lists.append(namelist)

        if func.__name__ == "translate":
            func(inputs_name_lists)
        else:
            with ThreadPool() as pool:
                pool.map(func, inputs_name_lists)

    except Exception as e:
        log.error(f"Error writing namelist file: {e}")
        log.debug(traceback.format_exc())
