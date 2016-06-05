
import os
import glob
import errno
import signal
import ctypes
import threading
from subprocess import check_output
from ast import literal_eval

ctypes_py_object = ctypes.py_object
ctypes_clong = ctypes.c_long
ctypes_py_thread_exec = ctypes.pythonapi.PyThreadState_SetAsyncExc

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty

from .patches import patchedglobals
from .utils import create_file_from_setup, timeout


class SetupThread(threading.Thread):

    def __init__(self, wrapper, setuppath, crash, result):
        threading.Thread.__init__(self)
        self.daemon = True
        self.wrapper = wrapper
        self.setuppath = setuppath
        self.crash = crash
        self.result = result

    def run(self):
        for pybin in glob.glob('/usr/bin/python?.?'):
            try:
                self.output = check_output([pybin, self.wrapper, self.setuppath],
                                           preexec_fn=os.setsid)
            except BaseException as e:
                self.crash.put(e)
            else:
                try:
                    setupargs = literal_eval(self.output)
                except BaseException as e:
                    self.crash.put(e)
                else:
                    self.result.put(setupargs)
                    break

    def stop(self):
        if not self.isAlive():
            return
        os.killpg(os.getpgid(self.output.pid), signal.SIGTERM)
        ctypes_py_thread_exec(ctypes_clong(self.ident),
                              ctypes_py_object(SystemExit))


def execute_setup(wrapper, setuppath):
    sec = 0
    crash = Queue()
    result = Queue()

    t = SetupThread(wrapper, setuppath, crash, result)
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

