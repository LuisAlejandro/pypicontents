# -*- coding: utf-8 -*-


import os
import re
import urlparse
import urllib


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
