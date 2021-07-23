from functools import partial
import re
import webbrowser

# (mss)
from PyQt5 import QtCore, QtGui, QtWidgets


TypeRole = QtCore.Qt.UserRole + 1


class DataType(object):
    """Base class for data types."""

    # (mss)
    COLOR = QtCore.Qt.black

    def matches(self, data):
        """Logic to define whether the given data matches this type."""
        raise NotImplementedError

    def next(self, model, data, parent):
        """Implement if this data type has to add child items to itself."""
        pass

    def actions(self, index):
        """Re-implement to return custom QActions."""
        return []

    def paint(self, painter, option, index):
        """Optionally re-implement for use by the delegate."""
        raise NotImplementedError

    def createEditor(self, parent, option, index):
        """Optionally re-implement for use by the delegate."""
        raise NotImplementedError

    def setModelData(self, editor, model, index):
        """Optionally re-implement for use by the delegate."""
        raise NotImplementedError

    def serialize(self, model, item, data, parent):
        """Serialize this data type."""
        value_item = parent.child(item.row(), 1)
        value = value_item.data(QtCore.Qt.DisplayRole)
        if isinstance(data, dict):
            key_item = parent.child(item.row(), 0)
            key = key_item.data(QtCore.Qt.DisplayRole)
            data[key] = value
        elif isinstance(data, list):
            data.append(value)

    def key_item(self, key, model, datatype=None, editable=True):
        """Create an item for the key column for this data type."""
        key_item = QtGui.QStandardItem(key)
        key_item.setData(datatype, TypeRole)
        key_item.setData(datatype.__class__.__name__, QtCore.Qt.ToolTipRole)
        key_item.setData(
            QtGui.QBrush(datatype.COLOR), QtCore.Qt.ForegroundRole)
        key_item.setFlags(
            QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
        if editable and model.editable_keys:
            key_item.setFlags(key_item.flags() | QtCore.Qt.ItemIsEditable)
        return key_item

    def value_item(self, value, model, key=None):
        """Create an item for the value column for this data type."""
        display_value = value
        item = QtGui.QStandardItem(display_value)
        item.setData(display_value, QtCore.Qt.DisplayRole)
        item.setData(value, QtCore.Qt.UserRole)
        item.setData(self, TypeRole)
        item.setData(QtGui.QBrush(self.COLOR), QtCore.Qt.ForegroundRole)
        item.setFlags(
            QtCore.Qt.ItemIsSelectable |
            QtCore.Qt.ItemIsEnabled)
        if model.editable_values:
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        return item


# -----------------------------------------------------------------------------
# Default Types
# -----------------------------------------------------------------------------


class NoneType(DataType):
    """None"""

    def matches(self, data):
        return data is None

    def value_item(self, value, model, key=None):
        item = super(NoneType, self).value_item(value, model, key)
        item.setData('None', QtCore.Qt.DisplayRole)
        return item

    def serialize(self, model, item, data, parent):
        value_item = parent.child(item.row(), 1)
        value = value_item.data(QtCore.Qt.DisplayRole)
        value = value if value != 'None' else None
        if isinstance(data, dict):
            key_item = parent.child(item.row(), 0)
            key = key_item.data(QtCore.Qt.DisplayRole)
            data[key] = value
        elif isinstance(data, list):
            data.append(value)


class StrType(DataType):
    """Strings and unicodes"""

    def matches(self, data):
        # (mss)
        return isinstance(data, str)


class IntType(DataType):
    """Integers"""

    def matches(self, data):
        return isinstance(data, int) and not isinstance(data, bool)


class FloatType(DataType):
    """Floats"""

    def matches(self, data):
        return isinstance(data, float)


class BoolType(DataType):
    """Bools are displayed as checkable items with a check box."""

    def matches(self, data):
        return isinstance(data, bool)

    def value_item(self, value, model, key=None):
        item = super(BoolType, self).value_item(value, model, key)
        item.setCheckState(QtCore.Qt.Checked if value else QtCore.Qt.Unchecked)
        item.setData('', QtCore.Qt.DisplayRole)
        if model.editable_values:
            item.setFlags(
                item.flags() | QtCore.Qt.ItemIsEditable |
                QtCore.Qt.ItemIsUserCheckable)
        return item

    def serialize(self, model, item, data, parent):
        value_item = parent.child(item.row(), 1)
        value = value_item.checkState() == QtCore.Qt.Checked
        if isinstance(data, dict):
            key_item = parent.child(item.row(), 0)
            key = key_item.data(QtCore.Qt.DisplayRole)
            data[key] = value
        elif isinstance(data, list):
            data.append(value)


class ListType(DataType):
    """Lists"""

    def matches(self, data):
        return isinstance(data, list)

    def next(self, model, data, parent):
        for i, value in enumerate(data):
            type_ = match_type(value)
            key_item = self.key_item(
                str(i), datatype=type_, editable=False, model=model)
            value_item = type_.value_item(value, model=model, key=str(i))
            parent.appendRow([key_item, value_item])
            type_.next(model, data=value, parent=key_item)

    def value_item(self, value, model, key):
        item = QtGui.QStandardItem()
        item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
        return item

    def serialize(self, model, item, data, parent):
        key_item = parent.child(item.row(), 0)
        if key_item:
            if isinstance(data, dict):
                key = key_item.data(QtCore.Qt.DisplayRole)
                data[key] = []
                data = data[key]
            elif isinstance(data, list):
                new_data = []
                data.append(new_data)
                data = new_data
        for row in range(item.rowCount()):
            child_item = item.child(row, 0)
            type_ = child_item.data(TypeRole)
            type_.serialize(
                model=self, item=child_item, data=data, parent=item)


class DictType(DataType):
    """Dictionaries"""

    def matches(self, data):
        return isinstance(data, dict)

    def next(self, model, data, parent):
        for key, value in data.items():
            type_ = match_type(value)
            key_item = self.key_item(key, datatype=type_, model=model)
            value_item = type_.value_item(value, model, key)
            parent.appendRow([key_item, value_item])
            type_.next(model, data=value, parent=key_item)

    def value_item(self, value, model, key):
        item = QtGui.QStandardItem()
        item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
        return item

    def serialize(self, model, item, data, parent):
        key_item = parent.child(item.row(), 0)
        if key_item:
            if isinstance(data, dict):
                key = key_item.data(QtCore.Qt.DisplayRole)
                data[key] = {}
                data = data[key]
            elif isinstance(data, list):
                new_data = {}
                data.append(new_data)
                data = new_data
        for row in range(item.rowCount()):
            child_item = item.child(row, 0)
            type_ = child_item.data(TypeRole)
            type_.serialize(model=self, item=child_item, data=data, parent=item)


# -----------------------------------------------------------------------------
# Derived Types
# -----------------------------------------------------------------------------


class RangeType(DataType):
    """A range, shown as three spinboxes next to each other.

    A range is defined as a dict with start, end and step keys.
    It supports both floats and ints.
    """

    KEYS = ['start', 'end', 'step']

    def matches(self, data):
        if isinstance(data, dict) and len(data) == 3:
            if all([True if k in self.KEYS else False for k in data.keys()]):
                return True
        return False

    def paint(self, painter, option, index):
        data = index.data(QtCore.Qt.UserRole)

        painter.save()

        painter.setPen(QtGui.QPen(index.data(QtCore.Qt.ForegroundRole).color()))
        metrics = painter.fontMetrics()
        spinbox_option = QtWidgets.QStyleOptionSpinBox()
        start_rect = QtCore.QRect(option.rect)
        start_rect.setWidth(start_rect.width() / 3.0)
        spinbox_option.rect = start_rect
        spinbox_option.frame = True
        spinbox_option.state = option.state
        spinbox_option.buttonSymbols = QtWidgets.QAbstractSpinBox.NoButtons
        for i, key in enumerate(self.KEYS):
            if i > 0:
                spinbox_option.rect.adjust(
                    spinbox_option.rect.width(), 0,
                    spinbox_option.rect.width(), 0)
            QtWidgets.QApplication.style().drawComplexControl(
                QtWidgets.QStyle.CC_SpinBox, spinbox_option, painter)
            value = str(data[key])
            value_rect = QtCore.QRectF(
                spinbox_option.rect.adjusted(6, 1, -2, -2))
            value = metrics.elidedText(
                value, QtCore.Qt.ElideRight, value_rect.width() - 20)
            painter.drawText(value_rect, value)

        painter.restore()

    def createEditor(self, parent, option, index):
        data = index.data(QtCore.Qt.UserRole)
        wid = QtWidgets.QWidget(parent)
        wid.setLayout(QtWidgets.QHBoxLayout(parent))
        wid.layout().setContentsMargins(0, 0, 0, 0)
        wid.layout().setSpacing(0)

        start = data['start']
        end = data['end']
        step = data['step']

        if isinstance(start, float):
            start_spinbox = QtWidgets.QDoubleSpinBox(wid)
        else:
            start_spinbox = QtWidgets.QSpinBox(wid)

        if isinstance(end, float):
            end_spinbox = QtWidgets.QDoubleSpinBox(wid)
        else:
            end_spinbox = QtWidgets.QSpinBox(wid)

        if isinstance(step, float):
            step_spinbox = QtWidgets.QDoubleSpinBox(wid)
        else:
            step_spinbox = QtWidgets.QSpinBox(wid)

        start_spinbox.setRange(-16777215, 16777215)
        end_spinbox.setRange(-16777215, 16777215)
        step_spinbox.setRange(-16777215, 16777215)
        start_spinbox.setValue(start)
        end_spinbox.setValue(end)
        step_spinbox.setValue(step)
        wid.layout().addWidget(start_spinbox)
        wid.layout().addWidget(end_spinbox)
        wid.layout().addWidget(step_spinbox)
        return wid

    def setModelData(self, editor, model, index):
        if isinstance(model, QtWidgets.QAbstractProxyModel):
            index = model.mapToSource(index)
            model = model.sourceModel()
        data = index.data(QtCore.Qt.UserRole)
        data['start'] = editor.layout().itemAt(0).widget().value()
        data['end'] = editor.layout().itemAt(1).widget().value()
        data['step'] = editor.layout().itemAt(2).widget().value()
        model.itemFromIndex(index).setData(data, QtCore.Qt.UserRole)

    def value_item(self, value, model, key=None):
        """Item representing a value."""
        value_item = super(RangeType, self).value_item(None, model, key)
        value_item.setData(value, QtCore.Qt.UserRole)
        return value_item

    def serialize(self, model, item, data, parent):
        value_item = parent.child(item.row(), 1)
        value = value_item.data(QtCore.Qt.UserRole)
        if isinstance(data, dict):
            key_item = parent.child(item.row(), 0)
            key = key_item.data(QtCore.Qt.DisplayRole)
            data[key] = value
        elif isinstance(data, list):
            data.append(value)


class UrlType(DataType):
    """Provide a link to urls."""

    REGEX = re.compile(r'(?:https?):\/\/|(?:file):\/\/')

    def matches(self, data):
        # (mss)
        if isinstance(data, str):
            if self.REGEX.match(data) is not None:
                return True
        return False

    def actions(self, index):
        explore = QtWidgets.QAction('Explore ...', None)
        explore.triggered.connect(
            partial(webbrowser.open, index.data(QtCore.Qt.DisplayRole)))
        return [explore]


class FilepathType(DataType):
    """Files and paths can be opened."""

    REGEX = re.compile(r'(\/.*)|([A-Z]:\\.*)')

    def matches(self, data):
        # (mss)
        if isinstance(data, str):
            if self.REGEX.match(data) is not None:
                return True
        return False

    def actions(self, index):
        explore = QtWidgets.QAction('Explore ...', None)
        path = index.data(QtCore.Qt.DisplayRole)
        explore.triggered.connect(partial(webbrowser.open, path))
        return [explore]


class ChoicesType(DataType):
    """A combobox that allows for a number of choices.

    The data has to be a dict with a value and a choices key.
    {
        "value": "A",
        "choices": ["A", "B", "C"]
    }
    """

    KEYS = ['value', 'choices']

    def matches(self, data):
        if isinstance(data, dict) and len(data) == 2:
            if all([True if k in self.KEYS else False for k in data.keys()]):
                return True
        return False

    def createEditor(self, parent, option, index):
        data = index.data(QtCore.Qt.UserRole)
        cbx = QtWidgets.QComboBox(parent)
        cbx.addItems([str(d) for d in data['choices']])
        cbx.setCurrentIndex(cbx.findText(str(data['value'])))
        return cbx

    def setModelData(self, editor, model, index):
        if isinstance(model, QtWidgets.QAbstractProxyModel):
            index = model.mapToSource(index)
            model = model.sourceModel()
        data = index.data(QtCore.Qt.UserRole)
        data['value'] = data['choices'][editor.currentIndex()]
        model.itemFromIndex(index).setData(data['value'] , QtCore.Qt.DisplayRole)
        model.itemFromIndex(index).setData(data, QtCore.Qt.UserRole)

    def value_item(self, value, model, key=None):
        """Item representing a value."""
        value_item = super(ChoicesType, self).value_item(value['value'], model, key)
        value_item.setData(value, QtCore.Qt.UserRole)
        return value_item

    def serialize(self, model, item, data, parent):
        value_item = parent.child(item.row(), 1)
        value = value_item.data(QtCore.Qt.UserRole)
        if isinstance(data, dict):
            key_item = parent.child(item.row(), 0)
            key = key_item.data(QtCore.Qt.DisplayRole)
            data[key] = value
        elif isinstance(data, list):
            data.append(value)


# Add any custom DataType to this list
#
DATA_TYPES = [
    NoneType(),
    UrlType(),
    FilepathType(),
    StrType(),
    IntType(),
    FloatType(),
    BoolType(),
    ListType(),
    RangeType(),
    ChoicesType(),
    DictType()
]


def match_type(data):
    """Try to match the given data object to a DataType"""
    for type_ in DATA_TYPES:
        if type_.matches(data):
            return type_
