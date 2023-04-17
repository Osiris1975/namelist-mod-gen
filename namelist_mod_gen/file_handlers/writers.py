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


def write_template(**kwargs):
    """
    Writes the jinaj2 template. The acceptable keyword args that may be used are as follows:
    :param dest_file: path where the file should be written
    :param render_dict: dictionary for use in template rendering
    :param template: the template to be rendered
    :param encoding: type of encoding to use (ex: utf-8)
    :param author: author of the file being written
    :param lang: language the associated render dict is in
    :return:
    """
    template = kwargs.get('template')
    dest_file = kwargs.get('dest_file')
    render_dict = kwargs.get('render_dict')
    author = kwargs.get('author')
    with io.open(dest_file, 'w', encoding=kwargs.get('encoding')) as file:
        if kwargs.get('lang'):
            name_list = template.render(dict_item=render_dict, lang=kwargs.get('lang'), author=author)
        else:
            name_list = template.render(dict_item=render_dict, author=author)
        file.write(name_list)
        log.info(f'Namelist file written to {dest_file}')


def ok_to_overwrite(namelist, dest_file):
    """
    Check if it's ok to overwite pre-existing files for a given namelist.
    :param namelist: The name of the namelist. Used solely for logging.
    :param dest_file: the destination of the file.
    :return: Boolean
    """
    if namelist['overwrite']:
        log.warning(f'Overwrite selected for {namelist["title"]}. Removing {dest_file}')
        if os.path.exists(dest_file):
            os.remove(dest_file)
        return True
    else:
        if os.path.exists(dest_file):
            log.warning(f'Overwrite not selected for {namelist["title"]}. Skipping writing of {dest_file}')
            return False
        else:
            return True
