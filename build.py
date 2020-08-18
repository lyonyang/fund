#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

import os
import time
import shutil
from distutils.core import setup
from Cython.Build import cythonize

ROOT_PATH = os.path.abspath('.')
PROJECT_NAME = ROOT_PATH.split('/')[-1]

# Ignore
EXCEPT_FILES = {
    'build.py'
}

# Only copy
IGNORE_FILES = {
    'run.py',
    'docs/view.py'
}

PY_FILE_EXCEPT_SUF = ('.pyc', '.pyx')
PY_FILE_SUF = ('.py')


def ls(dir=''):
    """Return all relative path under the current folder."""
    dir_path = os.path.join(ROOT_PATH, dir)
    for filename in os.listdir(dir_path):
        absolute_file_path = os.path.join(dir_path, filename)
        file_path = os.path.join(dir, filename)
        if filename.startswith('.'):
            continue
        if os.path.isdir(absolute_file_path) and not filename.startswith('__'):
            for file in ls(file_path):
                yield file
        else:
            yield file_path


def move_dist(dist):
    """Move dist/project_name -> dist/"""
    files = ls(dist)
    for file in files:
        src = os.path.join(ROOT_PATH, file)
        dst = os.path.join(ROOT_PATH, file.replace('/%s' % PROJECT_NAME, '', 1))
        dir = '/'.join(dst.split('/')[:-1])
        if not os.path.exists(dir):
            os.makedirs(dir)
        shutil.move(src, dst)
    if os.path.exists(os.path.join(dist, PROJECT_NAME)):
        shutil.rmtree(os.path.join(dist, PROJECT_NAME))


def copy_ignore(dist):
    """Copy exclude files"""
    files = ls()
    for file in files:
        if file.split('/')[0] == dist:
            continue
        suffix = os.path.splitext(file)[1]
        if file in IGNORE_FILES:
            pass
        elif not suffix:
            continue
        elif suffix in PY_FILE_EXCEPT_SUF:
            continue
        elif suffix in PY_FILE_SUF:
            continue
        src = os.path.join(ROOT_PATH, file)
        dst = os.path.join(ROOT_PATH, os.path.join(dist, PROJECT_NAME, file.replace(ROOT_PATH, '', 1)))
        dir = '/'.join(dst.split('/')[:-1])
        if not os.path.exists(dir):
            os.makedirs(dir)
        shutil.copyfile(src, dst)


def build(dist='dist'):
    """py -> c - so"""
    start = time.time()
    files = list(ls())
    module_list = list()
    for file in files:
        if file in EXCEPT_FILES or file in IGNORE_FILES:
            continue

        suffix = os.path.splitext(file)[1]
        if not suffix:
            continue
        elif suffix in PY_FILE_EXCEPT_SUF:
            continue
        elif suffix in PY_FILE_SUF:
            module_list.append(file)

    dist = os.path.join('.', dist)
    dist_temp = os.path.join(dist, 'temp')
    try:
        setup(ext_modules=cythonize(module_list, language_level="3"),
              script_args=["build_ext", "-b", dist, "-t", dist_temp])
    except Exception as e:
        print('Error: ', e)
        if os.path.exists(dist_temp):
            shutil.rmtree(dist_temp)
        for file in ls():
            if not file.endswith('.c'):
                continue
            os.remove(os.path.join(ROOT_PATH, file))
        return

    if os.path.exists(dist_temp):
        shutil.rmtree(dist_temp)
    for file in ls():
        if not file.endswith('.c'):
            continue
        os.remove(os.path.join(ROOT_PATH, file))

    copy_ignore(dist)
    end = time.time()
    print('Complete, %.2fs !' % (end - start))


if __name__ == '__main__':
    build('dist')
