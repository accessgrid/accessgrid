import win32gui, win32api, win32con
from DisplayTypes import Window

def Resize(window, width, height):
    hwnd = window.GetHandle()
    (x1, y1, x2, y2) = win32gui.GetWindowRect(hwnd)
    redraw = 1
    win32gui.MoveWindow(hwnd, x1, y1, width, height, redraw)
    window.width = width
    window.height = height

def Move(window, x, y):
    hwnd = window.GetHandle()
    (x1, y1, x2, y2) = win32gui.GetWindowRect(hwnd)
    width  = x2 - x1
    height = y2 - y1
    redraw = 1
    win32gui.MoveWindow(hwnd, x, y, width, height, redraw)
    window.x = x
    window.y = y

def Raise(window):
    win32gui.BringWindowToTop(window.GetHandle())

def GetWindowList():
    """
    """
    winList = list()
    wList = list()
    win32gui.EnumWindows(lambda hwnd, winlist: winlist.append(hwnd), wList)

    for hwnd in wList:
        if win32gui.IsWindowVisible(hwnd):
            (x1, y1, x2, y2) = win32gui.GetWindowRect(hwnd)
            if x2 > x1 and y2 > y1 and x1 > 0 and y1 > 0:
                title = win32gui.GetWindowText(hwnd)
                if title != "Program Manager":
                    winList.append(Window(x1, y1, x2-x1, y2-y1, title, hwnd))

    return winList
    
