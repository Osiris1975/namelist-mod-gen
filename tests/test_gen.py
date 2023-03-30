# Generated with help from ChatGPT
import unittest
from unittest.mock import MagicMock, create_autospec

import pytest

from execution.execute import write_common_name_lists, _write_common_namelist


@pytest.fixture
def name_lists():
    return {
        'directories': {
            'common': '/path/to/common/directory'
        },
        'namelist_template': MagicMock(),
        'overwrite': False,
        'namelists': {
            'namelist1': {
                'data': {
                    'namelist_title': ['Title1'],
                    'parameter1': ['value1'],
                    'parameter2': ['value2'],
                }
            },
            'namelist2': {
                'data': {
                    'namelist_title': ['Title2'],
                    'parameter1': ['value1'],
                    'parameter2': ['value2'],
                }
            }
        }
    }


class TestWriteCommonNameLists(unittest.TestCase):
    def test_no_namelists_key(self):
        input_dict = {'directories': {'common': '/path/to/common/files'}}
        with self.assertLogs('NMG', level='ERROR') as cm:
            write_common_name_lists(input_dict)
        self.assertEqual(cm.output[0], 'ERROR:NMG:Input dictionary does not contain "namelists" key')


def test_write_common_name_lists_calls__write_common_namelist_with_correct_args(monkeypatch, name_lists):
    mocked_write_common_namelist = create_autospec(_write_common_namelist)
    monkeypatch.setattr('gen.generate._write_common_namelist', mocked_write_common_namelist)
    write_common_name_lists(name_lists)
    assert mocked_write_common_namelist.call_count == 2


def test_write_common_name_lists_with_parallel_process_calls__write_common_namelist_with_correct_args(monkeypatch, name_lists):
    mocked_write_common_namelist = create_autospec(_write_common_namelist)
    monkeypatch.setattr('my_module._write_common_namelist', MagicMock())
    write_common_name_lists(name_lists, parallel_process=True)
    assert mocked_write_common_namelist.call_count == 2
    assert mocked_write_common_namelist.call_args_list[0][0][0]['id'] == 'namelist1'
    assert mocked_write_common_namelist.call_args_list[1][0][0]['id'] == 'namelist2'
