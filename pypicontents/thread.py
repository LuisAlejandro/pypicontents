
import errno
import Queue
import multiprocessing

from .patches import patchedglobals
from .utils import create_file_from_setup


class SetupProcess(multiprocessing.Process):

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
    sec = 0
    crash = Queue.Queue()
    result = Queue.Queue()
    setupcode = open(setuppath, 'rb').read()
    env = patchedglobals(setuppath)

    p = SetupProcess(setupcode, crash, result, env)
    p.start()


    while sec < 200:
        p.join(0.1)
        sec += 1

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
            return r
    else:
        p.terminate()
        raise TimeoutError

