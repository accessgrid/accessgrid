class NotImplementedException(Exception):
    '''
    Raised in super class when a method is missing
    in sub class.
    '''
    pass

class Model:
    def __init__(self):
        self.observers = []
    
    def RegisterObserver(self, observer):
        """
        Register an observer.
        
        @param observer: a callable object which update method
        will be invoked when state of this model changes.
        """
        #  log.debug("Register observer %s", observer)
        if observer not in self.observers:
            #   log.debug("Adding %s", observer)
            self.observers.append(observer)

    def UnregisterObserver(self, observer):
        """
        Unregister an observer.
        
        @param observer: The observer to be removed.
        """

        if observer in self.observers:
            self.observers.remove(observer)

    def NotifyObservers(self):
        """
        Send a notification to the observers.
        """
        
        removeList = []
        for observer in self.observers:
            if observer is None:
                # Object is gone, remove from list.
                removeList.append(observer)
            else:
                #try:
                #log.debug("NOTIFYing %s", obj)
                observer.Update()
                #except:
                #    #log.exception("Exception raised when calling observer %s", observer)
                #    removeList.append(observer)

        for observer in removeList:
            #log.info("Removing observer during NotifyObservers %s"%observer)
            self.observers.remove(observer)

class Observer:
    def __init__(self):
        pass
    
    def Update(self):
        raise NotImplementedError("Observer.Update")
