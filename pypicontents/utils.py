# -*- coding: utf-8 -*-


import os
import re
import sys
import urlparse
import urllib
import threading
import Queue
import unicodedata
import tokenize

import cStringIO as io


class SetupThread(threading.Thread):

    def __init__(self, code, crash, result, env):
        threading.Thread.__init__(self)
        self.who = env['__file__']
        self.code = code
        self.crash = crash
        self.result = result
        self.env = env

    def run(self):
        try:
            exec(compile(self.code, self.who, 'exec'), self.env, self.env)

        except BaseException:
            self.crash.put(sys.exc_info())
        else:
            self.result.put(setupargs)

def remove_comments_and_docstrings(source):
    io_obj = io.StringIO(source)
    tokens = list(tokenize.generate_tokens(io_obj.readline))
    out = ''

    for i, tok in enumerate(tokens):
        if i == 0:
            last_lineno = -1
            last_col = 0
            prev_toktype = ''
            next_toktype = tokens[i+1][0]

        elif i == len(tokens)-1:
            last_lineno = tokens[i-1][3][0]
            last_col = tokens[i-1][3][1]
            prev_toktype = tokens[i-1][0]
            next_toktype = ''

        else:
            last_lineno = tokens[i-1][3][0]
            last_col = tokens[i-1][3][1]
            prev_toktype = tokens[i-1][0]
            next_toktype = tokens[i+1][0]

        token_type = tok[0]
        token_string = tok[1]
        start_line, start_col = tok[2]
        end_line, end_col = tok[3]

        if start_line > last_lineno:
            last_col = 0
        if start_col > last_col:
            out += (" " * (start_col - last_col))

        if token_type == tokenize.COMMENT:
            pass
        elif token_type == tokenize.STRING:
            if prev_toktype != tokenize.INDENT:
                if prev_toktype != tokenize.NEWLINE:
                    if next_toktype == tokenize.OP:
                        out += token_string
        else:
            out += token_string

    return out


def patchsetup(setuppath, patchespath):
    futregex = r'(from\s*__future__\s*import\s*(?:\(.*?\)|.*?\n))'

    setuppyconts = open(setuppath, 'rb').read()
    patchesconts = open(patchespath, 'rb').read()

    futimports = re.findall(futregex, setuppyconts, flags=re.M|re.S)
    setuppyconts = re.sub(futregex, '', setuppyconts, flags=re.M|re.S)
    setuppyconts = '%s\n%s\n%s' % (''.join(futimports), patchesconts, setuppyconts)
    setuppyconts = unicodedata.normalize('NFKD', setuppyconts.decode('utf-8')).encode('ascii', 'ignore')
    setuppyconts = remove_comments_and_docstrings(unicode(setuppyconts))

    return '#!/usr/bin/env python\n%s' % setuppyconts


def execute_setup(setuppath, patchespath):
    crash = Queue.Queue()
    result = Queue.Queue()
    env = globals()
    env.update({'__file__': setuppath})
    patchedcode = patchsetup(setuppath, patchespath)

    t = SetupThread(patchedcode, crash, result, env)
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
            # print traceback.print_exception(etype, evalue, etrace)
            raise etype(evalue)

        t.join(0.1)

    return setupargs

def urlesc(url):
    parts=urlparse.urlparse(url)
    return urlparse.urlunparse(parts[:2] + (urllib.quote(parts[2]),) + parts[3:])

def get_archive_extension(path):
    extensions = []
    root, ext = os.path.splitext(path)
    while ext:
        extensions.append(ext)
        if ext == '.tar' or ext == '.zip' or ext == '.tgz':
            break
        root, ext = os.path.splitext(root)
    return ''.join(extensions[::-1])

def pygrep(pattern, dir):
    r = re.compile(pattern)
    for parent, dnames, fnames in os.walk(dir):
        for fname in fnames:
            filename = os.path.join(parent, fname)
            if os.path.isfile(filename):
                with open(filename) as f:
                    for line in f:
                        if r.search(line):
                            yield filename
