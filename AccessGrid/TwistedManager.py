# Most of this is from Twisted examples blockingdemo.py and pygamedemo.py
#   See Twisted license (MIT)

from Queue import Queue, Empty
import time
from twisted.internet import reactor
from itertools import count
from twisted.python.runtime import seconds
from twisted.internet.defer import Deferred
from twisted.python.failure import Failure

class TwistedManager(object):
    def __init__(self):
        self.twistedQueue = Queue()
        self.key = count()
        self.results = {}

    def getKey(self):
        # get a unique identifier
        return self.key.next()

    def start(self):
        # start the reactor
        reactor.interleave(self.twistedQueue.put)

    def _stopIterating(self, value, key):
        self.results[key] = value

    def stop(self):
        # stop the reactor
        key = self.getKey()
        reactor.addSystemEventTrigger('after', 'shutdown',
            self._stopIterating, True, key)
        reactor.stop()
        self.iterate(key)

    def getDeferred(self, d):
        # get the result of a deferred or raise if it failed
        key = self.getKey()
        d.addBoth(self._stopIterating, key)
        res = self.iterate(key)
        if isinstance(res, Failure):
            res.raiseException()
        return res


    def poll(self, noLongerThan=1.0):
        # poll the reactor for up to noLongerThan seconds
        base = seconds()
        try:
            while (seconds() - base) <= noLongerThan:
                callback = self.twistedQueue.get_nowait()
                callback()
        except Empty:
            pass

    def iterate(self, key=None):
        # iterate the reactor until it has the result we're looking for
        while key not in self.results:
            callback = self.twistedQueue.get()
            callback()
        return self.results.pop(key)


def fakeDeferred(msg):
    d = Deferred()
    def cb():
        print "deferred called back"
        d.callback(msg)
    reactor.callLater(0.05, cb)
    return d


#### pygame dependent version
# works, good for comparison testing/debugging with above method.
"""
import pygame
from pygame.locals import *

try:
    import pygame.fastevent as eventmodule
except ImportError:
    import pygame.event as eventmodule


# You can customize this if you use your
# own events, but you must OBEY:
#
#   USEREVENT <= TWISTEDEVENT < NUMEVENTS
#
TWISTEDEVENT = USEREVENT

def postTwistedEvent(func):
    # if not using pygame.fastevent, this can explode if the queue
    # fills up.. so that's bad.  Use pygame.fastevent, in pygame CVS
    # as of 2005-04-18.
    eventmodule.post(eventmodule.Event(TWISTEDEVENT, iterateTwisted=func))

def eventIterator():
    while True:
        yield eventmodule.wait()
        while True:
            event = eventmodule.poll()
            if event.type == NOEVENT:
                break
            else:
                yield event

from twisted.internet import reactor

def pygameTwistedLoop():
    pygame.init()
    if hasattr(eventmodule, 'init'):
        eventmodule.init()

    # send an event when twisted wants attention
    reactor.interleave(postTwistedEvent)
    # make shouldQuit a True value when it's safe to quit
    # by appending a value to it.  This ensures that
    # Twisted gets to shut down properly.
    shouldQuit = []
    reactor.addSystemEventTrigger('after', 'shutdown', shouldQuit.append, True)

    for event in eventIterator():
        if event.type == TWISTEDEVENT:
            event.iterateTwisted()
            if shouldQuit:
                break
        elif event.type == QUIT:
            reactor.stop()
        elif event.type == KEYDOWN and event.key == K_ESCAPE:
            reactor.stop()
                   
    pygame.quit()

"""
###
