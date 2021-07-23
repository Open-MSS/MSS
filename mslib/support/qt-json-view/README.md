# Qt JSON View

This widget allows to display and edit JSON-serializable data in a Qt view. The system is easily extensible with custom types.

An example to get you started is [here](example.py).

![Qt JSON View](qt-json-view.png)

## Overview

A provided JSON-serializable dict or list is [converted](qt_json_view/model.py#L18) to a [JsonModel](qt_json_view/model.py#L6) derived from QStandardItemModel.
During conversion, each entry in the source data is mapped to a [DataType](qt_json_view/datatypes.py#L11).
The [DataType](qt_json_view/datatypes.py#L11) defines how the entry is added to the [JsonModel](qt_json_view/model.py#L6), how it is serialized. The [JsonDelegate](qt_json_view/delegate.py#L6) draws on the optional [DataType](qt_json_view/datatypes.py#L11) implementations to display the item. The [DataType](qt_json_view/datatypes.py#L11) can also define custom right-click [QActions](qt_json_view/datatypes.py#L24) for the item.
The [JsonModel](qt_json_view/model.py#L6) can then be [serialized](qt_json_view/model.py#L29) back into a dictionary after editing.

## DataTypes

A number of data types are already implemented, but it is easy to implement and inject your own on the fly, please see section below.

**Standard JSON Types:**

* [NoneType](qt_json_view/datatypes.py#L85): None
* [BoolType](qt_json_view/datatypes.py#L108): bool
* [IntType](qt_json_view/datatypes.py#L115): int
* [FloatType](qt_json_view/datatypes.py#L122): float
* [StrType](qt_json_view/datatypes.py#L129): str and unicode
* [ListType](qt_json_view/datatypes.py#L156): list
* [DictType](qt_json_view/datatypes.py#L194): dict

**Custom Types:**

* [UrlType](qt_json_view/datatypes.py#L344): Detects urls and provides an "Explore ..." action opening the web browser.
* [FilepathType](qt_json_view/datatypes.py#L362): Detects file paths and provides an "Explore ..." action opening the file browser
* [RangeType](qt_json_view/datatypes.py#L235): A range is displayed in one row and has to be a dict in the form of, both floats and ints are allowed and displayed accordingly:
```json
{
    "start": 0,
    "end": 100,
    "step": 2.5
}
```

* [ChoicesType](qt_json_view/datatypes.py#L380): The user can choose from a range of choices. It is shown as a combobox. The data has to be a dict in the form:
```json
{
    "value": "A",
    "choices": ["A", "B", "C"]
}
```

### Implement custom DataTypes

Subclass the [DataType](qt_json_view/datatypes.py#L11) base class and implement what you need, at least the [matches](qt_json_view/datatypes.py#L16) method.
Then inject an instance of your DataType into [datatypes.DATA_TYPES](qt_json_view/datatypes.py#L433) so it is found when the model is initialized.
Make sure to inject it at the right position in the list [datatypes.DATA_TYPES](qt_json_view/datatypes.py#L433) list since the model uses the first match it finds.

```python
from qt_json_view import datatypes

class TestType(object):

    def matches(self, data):
        if data == "TEST":
            return True
        return False

idx = [i for i in datatypes.DATA_TYPES if isinstance(i, datatypes.StrType)][0]
datatypes.DATA_TYPES.insert(idx, TestType())
```

## View

The [JsonView](qt_json_view/view.py) is a QTreeView with the delegate.JsonDelegate.

## Model

The [JsonModel](qt_json_view/model.py) is a QStandardItemModel. It can be initialized from a JSON-serializable object and serialized to a JSON-serializable object.

## Filtering

The [JsonSortFilterProxyModel](qt_json_view/model.py#L41) is a QSortFilterProxyModel extended to filter through the entire tree.

## Delegate

The [JsonDelegate](qt_json_view/delegate.py) draws on the DataTypes of the items to determine how they are drawn. The [DataType](qt_json_view/datatypes.py#L11) uses the paint, createEditor and setModelData methods if they are available on the DataType.
