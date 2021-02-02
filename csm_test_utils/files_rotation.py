import hashlib
import logging
import os
import shutil
import sys
import time

import requests
from influx_line_protocol import Metric, MetricCollection
from ocomone.logging import setup_logger

from .parsers import AGP_SFS

SFS_COMPARE = "sfs_fcompare"

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


def report(args):
    try:
        create_file(base_file=f"{args.mount_point}/file.dat")
        result = 0
    except AssertionError:
        result = 1

    collection = MetricCollection()
    metric = Metric(SFS_COMPARE)
    metric.add_value("value", result)
    collection.append(metric)
    res = requests.post(f"{args.telegraf}/telegraf", data=str(collection), timeout=2)
    assert res.status_code == 204, f"Status is {res.status_code}"
    LOGGER.info("Metric written at: %s", args.telegraf)


def md5(file_name):
    hash_md5 = hashlib.md5()
    with open(file_name, "rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def create_file(dd_input="/dev/urandom", base_file="/tmp/base_file.data",
                size_bytes=1200000, count=100):
    base_copy = f"{base_file}_copy"
    modified_for_m = round((time.time() - os.path.getmtime(base_file)) / 60)
    if not os.path.exists(base_file) or modified_for_m > 60:
        shutil.rmtree(os.path.dirname(base_file))
        os.system(f"/bin/dd if={dd_input} of={base_file} bs={size_bytes} count={count}")
        LOGGER.info("Base file created at %s", base_file)
        base_hash = md5(base_file)
        try:
            shutil.copyfile(base_file, base_copy)
        except IOError:
            LOGGER.exception("Failed to copy file")
            raise
        LOGGER.info("Base file copied to %s", base_copy)
        copy_hash = md5(base_copy)
        assert base_hash == copy_hash, "Copy md5 differs"
    if int(time.strftime("%M")) % 5 == 0:
        base_hash = md5(base_file)
        copy_name = f"{base_file}_copy_{time.strftime('%H:%M')}"
        try:
            shutil.copyfile(base_copy, copy_name)
        except IOError:
            LOGGER.exception("Failed to copy file")
            raise
        LOGGER.info("Base file copied to %s", copy_name)
        copy_hash = md5(copy_name)
        assert base_hash == copy_hash, "Copy md5 differs"


def main():
    args, _ = AGP_SFS.parse_known_args()
    setup_logger(LOGGER, "sfs_fcompare", log_dir=args.log_dir,
                 log_format="[%(asctime)s] %(message)s")

    LOGGER.info("Started monitoring of NFS (telegraf at %s)", args.telegraf)
    while True:
        try:
            report(args)
            time.sleep(60)
        except KeyboardInterrupt:
            LOGGER.info("Monitoring \"sfs_compare\" Stopped")
            sys.exit(0)


if __name__ == "__main__":
    main()
