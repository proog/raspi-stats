import threading
from datetime import *
from util import *

class Repeater:
    def __init__(self, interval, action, name = 'Unnamed repeater', verbose = False):
        self.interval = interval
        self.action = action
        self.name = name
        self.verbose = verbose

    def schedule(self):
        next = datetime.now() + timedelta(seconds = self.interval)
        log('%s executing in %ds (%s)' % (self.name, self.interval, format_time(next)), self.verbose)

        t = threading.Timer(self.interval, self.run)
        t.daemon = True
        t.start()
        return t

    def run(self):
        log('%s executing...' % self.name, self.verbose)
        self.action()
        log('%s finished' % self.name, self.verbose)
        self.schedule()
