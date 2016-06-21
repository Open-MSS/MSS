import paste.util.multidict


class CaseInsensitiveMultiDict(paste.util.multidict.MultiDict):
    """Extension to paste.util.multidict.MultiDict that makes the MultiDict
       case-insensitive.

    The only overridden method is __getitem__(), which converts string keys
    to lower case before carrying out comparisons.

    See ../paste/util/multidict.py as well as
      http://stackoverflow.com/questions/2082152/case-insensitive-dictionary
    """

    def __getitem__(self, key):
        if hasattr(key, 'lower'):
            key = key.lower()
        for k, v in self._items:
            if hasattr(k, 'lower'):
                k = k.lower()
            if k == key:
                return v
        raise KeyError(repr(key))
