from AccessGrid.GUID import GUID

class Geometry:
    def __init__(self, x, y, width, height):
        self.x      = x
        self.y      = y
        self.width  = width
        self.height = height
#        self.x2     = x + width
#        self.y2     = y + height

    def __str__(self):
        return "(%d, %d) %d x %d" % (self.x, self.y, self.width, self.height)

    def x2(self):
        return self.x + self.width

    def y2(self):
        return self.y + self.height

    def GetSize(self):
        """
        Get the size of the window.

        @returns: (integer, integer)
        """
        return (self.width, self.height)
    
    def GetX(self):
        """
        Get the location of the x side of the window.

        @returns: integer
        """
        return self.x
    
    def GetY(self):
        """
        Get the location of the y side of the window.

        @returns: integer
        """
        return self.y

    def GetWidth(self):
        """
        Get the width.

        @returns: integer
        """
        return self.width

    def GetHeight(self):
        """
        Get the height.

        @returns: integer
        """
        return self.height

    def GetLocation(self):
        """
        Get the location of the window. This is a tuple of (x, y).

        @returns: (integer, integer)
        """
        return (self.x, self.y)

    def GetGeometry(self):
        """
        Get the geometry of the object, this is a tupe of (x, y,
        width, height).

        @returns: (integer, integer, integer, integer)
        """
        return (self.x, self.y, self.width, self.height)

class WindowSpec(Geometry):
    """
    This class is used to maintain an implementation independant
    handle on a window. This only contains the minimum of information
    for doing display related operations.

    The data contained in the window spec includes:

    @var wid : a unique identifier for this window
    @type wid : a string containing a unique id

    @var x : the location of the left side of the window
    @var y : the location of the top side of the window
    @var width : the width of the window
    @var height : the width of the window

    @type x : integer
    @type y : integer
    @type width : integer
    @type height : integer
    """
    def __init__(self, x, y, width, height, wid=str(GUID())):
        """
        The constructor.
        """
        Geometry.__init__(self, x, y, width, height)
        self.id = wid

    def __str__(self):
        return "%s: %s" % (self.title, Geometry.__str__(self))

    def GetId(self):
        """
        Return the id of the window.

        @returns: the identifying string of the window
        """
        return self.id

class Window:
    def __init__(self, x, y, width, height, title = "", handle = None):
        self.handle = handle
        self.title = title
        self.spec = WindowSpec(x, y, width, height)

    def GetHandle(self):
        return self.handle

    def GetTitle(self):
        return self.title
    
    def __str__(self):
        return "%s: %s" % (self.title, self.spec)

class Region(Geometry):
    """
    A region represents a portion of a display. It can be used to
    identify a valid location to place windows.

    @var rid: a unique identifer for the region
    @var left: the location of the left side of the region
    @var right: the location of the right side of the region
    @var top: the location of the top side of the region
    @var bottom: the location of the bottom side of the region

    @type rid: a string
    @type x: integer
    @type y: integer
    @type width: integer
    @type height: integer
    """
    def __init__(self, rid, x, y, width, height):
        """
        The standard constructor.
        """
        Geometry.__init__(self, x, y, width, height)
        self.id = rid

    def GetId(self):
        """
        Return the id of the region.

        @returns: string
        """
        return self.id

class Layout:
    """
    A layout represents a set of choices that map a set of windows
    represented by the window specs onto a set of regions represented
    by the regions.

    @var regions: a list of regions
    @var wspecs: a list of window specs
    @var layout: a dictionary of region => list of window specs

    @type regions: a list of Region objects
    @type wspecs: a list of WindowSpec objects
    @type layout: a dictionary mapping a Region to a list of WindowSpec objects
    """
    def __init__(self):
        """
        The standard constructor.
        """
        pass

    def GetRegions(self):
        """
        Retrieve the set of regions in this layout.

        @returns: a list of Region objects.
        """
        return self.regions
    
    def AddRegion(self, region):
        """
        Add a region to the list of regions in this layout.

        @param region: a region to be added.
        @type region: a Region object
        """
        self.regions.append(region)

    def RemoveRegion(self, region):
        """
        Remove a region from the list of regions in this layout.

        @param region: a region to be removed.
        @type region: a Region object
        """
        pass

    def GetWindows(self):
        """
        Retrieve the set of window specs in this layout.

        @returns: a list of WindowSpec objects.
        """
        return self.wspecs
    
    def AddWindow(self, wspec):
        """
        Add a window to the list of windows in this layout.

        @param window: a window to be added.
        @type window: a WindowSpec object
        """
        pass
    
    def RemoveWindow(self, wspec):
        """
        Remove a window from the list of windows in this layout.

        @param window: a window to be removed.
        @type window: a WindowSpec object
        """
        pass

    def GetLayout(self):
        """
        Retrieve the current layout.

        @returns: a dictionary of Region to list of WindowSpec objects.
        """
        return self.regionMap

    def SetLayout(self, regionMap):
        """
        Set the current region map to the one specified.

        This should be doing error checking to make sure that everything in
        the specified layout is in the layouts list of regions and windows.

        @param regionMap: the new region map
        @type regionMap: a dictionary of regions to window spec objects.
        """
        pass
    
