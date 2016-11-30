import os
import fnmatch
import shutil


def find_files(path=None, pattern='*'):
    """
    Locate all the files matching the supplied ``pattern`` in ``path``.

    Locate all the files matching the supplied filename pattern in and below
    the supplied root directory. If no pattern is supplied, all files will be
    returned.

    :param path: a string containing a path where the files will be looked for.
    :param pattern: a string containing a regular expression.
    :return: a list of files matching the pattern within path (recursive).

    .. versionadded:: 0.1
    """
    assert isinstance(path, basestring)
    assert isinstance(pattern, basestring)

    filelist = []
    for directory, subdirs, files in os.walk(os.path.normpath(path)):
        for filename in fnmatch.filter(files, pattern):
            if os.path.isfile(os.path.join(directory, filename)):
                filelist.append(os.path.join(directory, filename))
    return filelist


def find_dirs(path=None, pattern='*'):
    d = []
    assert type(path) == str
    assert type(pattern) == str

    for directory, subdirs, files in os.walk(os.path.normpath(path)):
        for subdir in fnmatch.filter(subdirs, pattern):
            if os.path.isdir(os.path.join(directory, subdir)):
                d.append(os.path.join(directory, subdir))
    return d


if __name__ == '__main__':

    jsondict = {}
    tars = []
    basedir = os.path.dirname(__file__)
    pipdir = os.path.join(os.environ.get('HOME'), '.cache', 'pip2')

    if not os.path.isdir(pipdir):
        os.makedirs(pipdir)

    for _dir in find_dirs(pipdir):
        if os.path.isdir(_dir):
            shutil.rmtree(_dir)

    tars = find_files(pipdir)

    # for _file in tars:
        
        
