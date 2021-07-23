# (mss)
from PyQt5 import QtWidgets, QtCore

from qt_json_view.datatypes import DataType, TypeRole


class JsonDelegate(QtWidgets.QStyledItemDelegate):
    """Display the data based on the definitions on the DataTypes."""

    def sizeHint(self, option, index):
        return QtCore.QSize(option.rect.width(), 20)

    def paint(self, painter, option, index):
        """Use method from the data type or fall back to the default."""
        if index.column() == 0:
            return super(JsonDelegate, self).paint(painter, option, index)
        type_ = index.data(TypeRole)
        if isinstance(type_, DataType):
            try:
                super(JsonDelegate, self).paint(painter, option, index)
                return type_.paint(painter, option, index)
            except NotImplementedError:
                pass
        return super(JsonDelegate, self).paint(painter, option, index)

    def createEditor(self, parent, option, index):
        """Use method from the data type or fall back to the default."""
        if index.column() == 0:
            return super(JsonDelegate, self).createEditor(
                parent, option, index)
        try:
            return index.data(TypeRole).createEditor(parent, option, index)
        except NotImplementedError:
            return super(JsonDelegate, self).createEditor(
                parent, option, index)

    def setModelData(self, editor, model, index):
        """Use method from the data type or fall back to the default."""
        if index.column() == 0:
            return super(JsonDelegate, self).setModelData(editor, model, index)
        try:
            return index.data(TypeRole).setModelData(editor, model, index)
        except NotImplementedError:
            return super(JsonDelegate, self).setModelData(editor, model, index)
