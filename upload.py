#!/usr/bin/env python
import sys
import json
import os

from internetarchive import get_item


def upload_item(item_dir):
    all_files = ['{0}/{1}'.format(item_dir, x) for x in os.listdir(item_dir)]

    # Make sure the item has at the very least a PDF and metadata.
    required_files = ['{0}/{0}.pdf'.format(item_dir), '{0}/{0}.json'.format(item_dir)]
    for required_file in required_files:
        assert any(f == required_file for f in all_files)

    # Parse metadata.
    json_md = '{0}/{0}.json'.format(item_dir)
    with open(json_md) as fp:
        md = json.load(fp)
    assert 'collection' in md

    # We don't want to upload the JSON file, remove it from all_files.
    files = [x for x in all_files if x != '{0}/{0}.json'.format(item_dir)]

    item = get_item(item_dir)
    rs = item.upload(files, metadata=md, retries=100, delete=True, checksum=True)
    if all(r.status_code == 200 for r in rs):
        with open('uploaded', 'a'):
            os.utime('uploaded', None)
    return rs


if __name__ == '__main__':
    item_dir = sys.argv[-1].strip('./')
    upload_item(item_dir)
