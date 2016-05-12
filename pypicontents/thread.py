
import sys
import threading
import Queue

from .patches import patchedglobals


class SetupThread(threading.Thread):

    def __init__(self, code, crash, result, env):
        threading.Thread.__init__(self)
        self.who = env['__file__']
        self.code = code
        self.crash = crash
        self.result = result
        self.env = env

    def run(self):
        setupargs = []
        try:
            exec(compile(self.code, self.who, 'exec'), self.env, self.env)
        except BaseException:
            self.crash.put(sys.exc_info())
        else:
            self.result.put(setupargs)

def execute_setup(setuppath, patchespath):
    crash = Queue.Queue()
    result = Queue.Queue()
    setupcode = open(setuppath, 'rb').read()
    env = patchedglobals(setuppath)

    t = SetupThread(setupcode, crash, result, env)
    t.start()

    while True:
        r = ''
        e = ''

        try:
            r = result.get(block=False)
        except Queue.Empty:
            pass
        else:
            setupargs = r
            break

        try:
            e = crash.get(block=False)
        except Queue.Empty:
            pass
        else:
            etype, evalue, etrace = e
            raise etype(evalue)

        t.join(0.1)

    return setupargs

