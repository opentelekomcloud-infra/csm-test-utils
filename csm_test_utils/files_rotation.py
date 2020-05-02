import logging
import shutil
import time

import hashlib
import os
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
    collection = MetricCollection()
    metric = Metric(SFS_COMPARE)
    metric.add_value("result", result)
    collection.append(metric)
    res = requests.post(f"{args.telegraf}/telegraf", data=str(collection), timeout=2)
    assert res.status_code == 204, f"Status is {res.status_code}"


def md5(file_name):
    hash_md5 = hashlib.md5()
    with open(file_name, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def create_file(dd_input="/dev/urandom", base_file="/tmp/base_file.data", bs=1200000, count=100):
    if not os.path.exists(base_file) or (round(time.time() - os.path.getmtime(base_file)) / 60) > 60:
        os.system(f"rm {base_file.split('.')[0]}*")
        os.system(f"/bin/dd if={dd_input} of={base_file} bs={bs} count={count}")
        base_hash = md5(base_file)
        copy_name = f"{base_file}_copy_{time.strftime('%H:%M')}"
        shutil.copyfile(base_file, copy_name)
        copy_hash = md5(copy_name)
        if base_hash == copy_hash:
            return "Hash of Base File and Copy are Equal"
        else:
            return "Hash of Base File and Copy are not Equal"
    else:
        base_hash = md5(base_file)
        copy_name = f"{base_file}_copy_{time.strftime('%H:%M')}"
        shutil.copyfile(base_file, copy_name)
        copy_hash = md5(copy_name)
        if base_hash == copy_hash:
            return "Hash of Base File and Copy are Equal"
        else:
            return "Hash of Base File and Copy are not Equal"


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
