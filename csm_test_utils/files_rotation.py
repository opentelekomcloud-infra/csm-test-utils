import hashlib
import logging
import os
import shutil
import sys
import time

import requests
from influx_line_protocol import Metric, MetricCollection
from ocomone.logging import setup_logger

from .common import base_parser, sub_parsers

SFS_COMPARE = "sfs_fcompare"

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

AGP = sub_parsers.add_parser("sfs_compare", add_help=False, parents=[base_parser])
AGP.add_argument("--mount_point", help="point where NFS mounted", default="/mnt/sfs_share", type=str)


def report(args):
    result = create_file(base_file=f"{args.mount_point}/file.dat")
    if result is not None:
        collection = MetricCollection()
        metric = Metric(SFS_COMPARE)
        metric.add_value("value", result)
        collection.append(metric)
        res = requests.post(f"{args.telegraf}/telegraf", data=str(collection), timeout=2)
        assert res.status_code == 204, f"Status is {res.status_code}"
        LOGGER.info(f"Metric written at: {args.telegraf})")


def md5(file_name):
    hash_md5 = hashlib.md5()
    with open(file_name, "rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def create_file(dd_input="/dev/urandom", base_file="/tmp/base_file.data", bs=1200000, count=100):
    base_copy = f"{base_file}_copy"
    if not os.path.exists(base_file) or (round(time.time() - os.path.getmtime(base_file)) / 60) > 60:
        for root, _, files in os.walk(os.path.dirname(base_file)):
            for file in files:
                os.remove(os.path.join(root, file))
        os.system(f"/bin/dd if={dd_input} of={base_file} bs={bs} count={count}")
        LOGGER.info(f"Base file created at {base_file}")
        base_hash = md5(base_file)
        try:
            shutil.copyfile(base_file, base_copy)
        except IOError as Error:
            LOGGER.error(Error)
            return
        LOGGER.info(f"Base file copied to {base_copy}")
        copy_hash = md5(base_copy)
        return int(base_hash != copy_hash)
    if int(time.strftime('%M')) % 5 == 0:
        base_hash = md5(base_file)
        copy_name = f"{base_file}_copy_{time.strftime('%H:%M')}"
        try:
            shutil.copyfile(base_copy, copy_name)
        except IOError as Error:
            LOGGER.error(Error)
            return
        LOGGER.info(f"Base file copied to {copy_name}")
        copy_hash = md5(copy_name)
        return int(base_hash != copy_hash)
    md5(base_file)


def main():
    args, _ = AGP.parse_known_args()
    setup_logger(LOGGER, "sfs_fcompare", log_dir=args.log_dir, log_format="[%(asctime)s] %(message)s")

    LOGGER.info(f"Started monitoring of NFS (telegraf at {args.telegraf})")
    while True:
        try:
            report(args)
            time.sleep(60)
        except KeyboardInterrupt:
            LOGGER.info("Monitoring Stopped")
            sys.exit(0)


if __name__ == "__main__":
    main()
