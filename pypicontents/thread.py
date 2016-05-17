
import errno
import threading
import Queue

from .patches import patchedglobals
from .utils import create_file_from_setup


class SetupThread(threading.Thread):

    def __init__(self, code, crash, result, env):
        threading.Thread.__init__(self)
        self.who = env['__file__']
        self.code = code
        self.crash = crash
        self.result = result
        self.env = env

    def run(self):
        while True:
            try:
                exec(compile(self.code, self.who, 'exec'), self.env)
            except BaseException as e:
                if (type(e) is IOError or type(e) is OSError
                    and e.errno is errno.ENOENT and e.filename):
                    create_file_from_setup(self.who, e.filename)
                else:
                    self.crash.put(e)
                    break
            else:
                self.result.put(self.env['setupargs'])
                break


def execute_setup(setuppath):
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
            try:
                e = crash.get(block=False)
            except Queue.Empty:
                pass
            else:
                raise e
        else:
            setupargs = r
            break

        t.join(0.1)

    return setupargs

