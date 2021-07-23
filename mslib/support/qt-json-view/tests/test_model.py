import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


from qt_json_view import datatypes, model


def test_none():
    assert datatypes.NoneType().matches(None)


def test_str():
    assert datatypes.StrType().matches('string')
    assert datatypes.StrType().matches(u'unicode')


def test_int():
    assert datatypes.IntType().matches(1)
    assert not datatypes.IntType().matches(True)
    assert not datatypes.IntType().matches(False)


def test_float():
    assert datatypes.FloatType().matches(1.234)


def test_bool():
    assert datatypes.BoolType().matches(True)
    assert datatypes.BoolType().matches(False)
    assert not datatypes.BoolType().matches(1.0)
    assert not datatypes.BoolType().matches(0)
    assert not datatypes.BoolType().matches(1)


def test_list():
    assert datatypes.ListType().matches(['1', 2, 3.0])


def test_dict():
    assert datatypes.DictType().matches({'a': 'b'})


def test_range():
    assert datatypes.RangeType().matches({
        'start': 0, 'end': 100, 'step': 1
    })
    assert datatypes.RangeType().matches({
        'start': 0.1, 'end': 100, 'step': 0.5
    })
    assert not datatypes.RangeType().matches({
        'start': 0, 'end': 100
    })


def test_url():
    assert datatypes.UrlType().matches('http://www.python.com')
    assert datatypes.UrlType().matches(u'https://www.python.com')
    assert datatypes.UrlType().matches(u'file:///some/file/path')
    assert datatypes.UrlType().matches(u'file://C:\\some-file.txt')


def test_filepath():
    assert datatypes.FilepathType().matches('/some/file/path')
    assert datatypes.FilepathType().matches('C:\\')
    assert datatypes.FilepathType().matches(u'/some/file.txt')
    assert datatypes.FilepathType().matches(u'C:\\some-file.txt')


def test_choices():
    assert datatypes.ChoicesType().matches({'value': 1, 'choices': [1, 2, 3, 4]})
    assert datatypes.ChoicesType().matches({'value': 'A', 'choices': ['A', 'B', 'C']})
    assert datatypes.ChoicesType().matches({'value': None, 'choices': ['A', 'B', 'C']})


DICT_DATA = {
    'none': None,
    'bool': True,
    'int': 666,
    'float': 1.23,
    'list1': [
        1,
        2
    ],
    'dict': {
        'key': 'value',
        'another_dict': {
            'a': 'b'
        }
    },

    # Custom types
    #
    'choice (str)': {
        'value': 'A',
        'choices': ['A', 'B', 'C']
    },
    'choice (int)': {
        'value': 1,
        'choices': [1, 2, 3]
    },
    'choice None': {
        'value': None,
        'choices': ['A', 'B']
    },
    'range': {
        'start': 0,
        'end': 100,
        'step': 0.5
    },

    'http': 'http://www.python.com',
    'https': 'https://www.python.com',
    'url (file)': 'file://{0}'.format(__file__),
    'filepath folder': os.path.dirname(__file__),
    'filepath file': __file__
}

LIST_DATA = [
    None,
    True,
    0,
    1,
    2,
    [
        'A',
        'B'
    ],
    {
        'value': 'A',
        'choices': ['A', 'B', 'C']
    },
    {
        'start': 0,
        'end': 100,
        'step': 0.5
    },
    'http://www.python.com',
    'https://www.python.com',
    'file://{0}'.format(__file__),
    os.path.dirname(__file__),
    __file__,
    DICT_DATA
]


def test_serialize_model():
    json_model = model.JsonModel(data=DICT_DATA, editable_keys=True, editable_values=True)
    serialized = json_model.serialize()
    assert DICT_DATA == serialized

    json_model = model.JsonModel(data=LIST_DATA, editable_keys=True, editable_values=True)
    serialized = json_model.serialize()
    assert LIST_DATA == serialized
