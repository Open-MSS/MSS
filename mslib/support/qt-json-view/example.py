from functools import partial
import json
import os

from Qt import QtWidgets

from qt_json_view import model
from qt_json_view.model import JsonModel
from qt_json_view.view import JsonView


dict_data = {
    # Defaut JSON Types
    #
    'none': None,
    'bool': True,
    'int': 666,
    'float': 1.23,
    'list1': [
        1,
        2,
        3,
        {
            'd': [
                4, 5, 6
            ]
        }
    ],
    'dict': {
        'key': 'value',
        'another_dict': {
            'a': 'b'
        }
    },

    # Custom Types
    #
    'url (http)': 'http://www.python.com',
    'url (https)': 'https://www.python.com',
    'url (file)': 'file://{0}'.format(__file__),
    'filepath (folder)': os.path.dirname(__file__),
    'filepath (file)': __file__,
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
    }
}


if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    widget = QtWidgets.QWidget()
    widget.setLayout(QtWidgets.QVBoxLayout())

    filter_widget = QtWidgets.QWidget()
    filter_widget.setLayout(QtWidgets.QHBoxLayout())

    filter_label = QtWidgets.QLabel('Filter:')
    filter_widget.layout().addWidget(filter_label)

    filter_text = QtWidgets.QLineEdit()
    filter_widget.layout().addWidget(filter_text)

    filter_column = QtWidgets.QComboBox()
    filter_column.addItems(['Key', 'Value'])
    filter_widget.layout().addWidget(filter_column)

    sort_button = QtWidgets.QPushButton('Sort')
    filter_widget.layout().addWidget(sort_button)

    widget.layout().addWidget(filter_widget)

    view = JsonView()
    widget.layout().addWidget(view)

    button = QtWidgets.QPushButton('Serialize')
    widget.layout().addWidget(button)

    proxy = model.JsonSortFilterProxyModel()

    model = JsonModel(data=dict_data, editable_keys=True, editable_values=True)
    proxy.setSourceModel(model)
    view.setModel(proxy)

    def filter_():
        proxy.setFilterKeyColumn(filter_column.currentIndex())
        proxy.setFilterRegExp(filter_text.text())
        view.expandAll()

    def serialize():
        print(json.dumps(model.serialize(), indent=2))

    button.clicked.connect(serialize)
    filter_text.textChanged.connect(filter_)
    filter_column.currentIndexChanged.connect(filter_)
    sort_button.clicked.connect(partial(proxy.sort, 0))

    widget.show()
    view.expandAll()

    app.exec_()
