
import errno
import ctypes
import threading

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty

from .patches import patchedglobals
from .utils import create_file_from_setup, timeout


class SetupThread(threading.Thread):

    def __init__(self, crash, result, env):
        threading.Thread.__init__(self)
        self.code = open(env['__file__'], 'rb').read()
        self.who = env['__file__']
        self.crash = crash
        self.result = result
        self.env = env

    def run(self):
        while True:
            try:
                exec(compile(self.code, self.who, 'exec'), self.env)
            except BaseException as e:
                if (type(e) == IOError or type(e) == OSError
                    and e.errno == errno.ENOENT and e.filename):
                    create_file_from_setup(self.who, e.filename)
                else:
                    self.crash.put(e)
                    break
            else:
                self.result.put(self.env['setupargs'])
                break

    def stop(self):
        if not self.isAlive():
            return

        e = ctypes.py_object(SystemExit)
        r = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self.ident), e)

        if r == 0:
            raise ValueError("nonexistent thread id")
        elif r > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")


def execute_setup(setuppath):
    sec = 0
    crash = Queue()
    result = Queue()
    env = patchedglobals(setuppath)

    t = SetupThread(crash, result, env)
    t.start()

    while sec < 200:
        t.join(0.1)
        sec += 1

        try:
            r = result.get(block=False)
        except Empty:
            try:
                e = crash.get(block=False)
            except Empty:
                pass
            else:
                raise e
        else:
            return r
    else:
        t.stop()
        raise RuntimeError('Execution of setup took too much time.')

