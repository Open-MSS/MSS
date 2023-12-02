import sys


def platform_keys():
    """
    Returns platform specific key mappings.

    Returns:
        A tuple containing the key mappings for the current platform.

    Note:
        The key mappings returned depend on the value of `sys.platform`.
        For Linux, the return values are ('ctrl', 'enter', 'winleft', 'altleft').
        For Windows, the return values are ('ctrl', 'enter', 'win', 'alt').
        For macOS, the return values are ('command', 'return').

    Example:
        ctrl, enter, win, alt = platform_keys()
    """
    #  sys.platform specific keyse
    if sys.platform == 'linux' or sys.platform == 'linux2':
        enter = 'enter'
        win = 'winleft'
        ctrl = 'ctrl'
        alt = 'altleft'
    elif sys.platform == 'win32':
        enter = 'enter'
        win = 'win'
        ctrl = 'ctrl'
        alt = 'alt'
    elif sys.platform == 'darwin':
        enter = 'return'
        ctrl = 'command'
    return ctrl, enter, win, alt
