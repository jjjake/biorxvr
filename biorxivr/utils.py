#!/usr/bin/env python
import sys
import os
import shutil


def delete_archived_item_dirs():
    for item in open(sys.argv[-1]):
        try:
            files = os.listdir(item.strip())
        except OSError:
            continue
        if files == ['{0}.json'.format(item.strip())]:
            shutil.rmtree(item.strip())


if __name__ == '__main__':
    if sys.argv[-1] == 'clean':
        delete_archived_item_dirs()
