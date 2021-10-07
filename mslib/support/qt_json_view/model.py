# (mss)
from PyQt5 import QtGui, QtCore

# (mss)
from mslib.support.qt_json_view.datatypes import match_type, TypeRole, ListType, DictType


class JsonModel(QtGui.QStandardItemModel):
    """Represent JSON-serializable data."""

    def __init__(
            self, parent=None,
            data=None,
            editable_keys=False,
            editable_values=False):
        super(JsonModel, self).__init__(parent=parent)
        if data is not None:
            self.init(data, editable_keys, editable_values)

    def init(self, data, editable_keys=False, editable_values=False):
        """Convert the data to items and populate the model."""
        self.clear()
        self.setHorizontalHeaderLabels(['Key', 'Value'])
        self.editable_keys = editable_keys
        self.editable_values = editable_values
        parent = self.invisibleRootItem()
        type_ = match_type(data)
        parent.setData(type_, TypeRole)
        type_.next(model=self, data=data, parent=parent)

    def serialize(self):
        """Assemble the model back into a dict or list."""
        parent = self.invisibleRootItem()
        type_ = parent.data(TypeRole)
        if isinstance(type_, ListType):
            data = []
        elif isinstance(type_, DictType):
            data = {}
        type_.serialize(model=self, item=parent, data=data, parent=parent)
        return data


class JsonSortFilterProxyModel(QtCore.QSortFilterProxyModel):  # (mss)
    """Show ALL occurences by keeping the parents of each occurence visible."""

    def filterAcceptsRow(self, sourceRow, sourceParent):
        """Accept the row if the parent has been accepted."""
        index = self.sourceModel().index(sourceRow, self.filterKeyColumn(), sourceParent)
        return self.accept_index(index)

    def accept_index(self, index):
        if index.isValid():
            text = str(index.data(self.filterRole()))
            if self.filterRegExp().indexIn(text) >= 0:
                return True
            for row in range(index.model().rowCount(index)):
                if self.accept_index(index.model().index(row, self.filterKeyColumn(), index)):
                    return True
        return False
