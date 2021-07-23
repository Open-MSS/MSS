from Qt import QtCore, QtWidgets

from qt_json_view import delegate
from qt_json_view.datatypes import TypeRole


class JsonView(QtWidgets.QTreeView):
    """Tree to display the JsonModel."""

    def __init__(self, parent=None):
        super(JsonView, self).__init__(parent=parent)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu)
        self.setItemDelegate(delegate.JsonDelegate())

    def _menu(self, position):
        """Show the actions of the DataType (if any)."""
        menu = QtWidgets.QMenu()
        index = self.indexAt(position)
        data = index.data(TypeRole)
        if data is None:
            return
        for action in data.actions(index):
            menu.addAction(action)
        menu.exec_(self.viewport().mapToGlobal(position))
