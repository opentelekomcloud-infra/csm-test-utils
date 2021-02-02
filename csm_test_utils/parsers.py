"""All argument parsers"""
import os
from argparse import ArgumentParser

_base_parser = ArgumentParser(prog="csm_test_utils", description="Multi-purpose test script")
"""Base for all parsers"""

_base_parser.add_argument("--target", help="Load balancer address")
__tgf_default = os.getenv("TGF_ADDRESS", "")
_base_parser.add_argument("--telegraf",
                          help=f"Address of telegraf server for reporting. "
                               f"Default is taken from TGF_ADDRESS variable ('{__tgf_default}')",
                          default=__tgf_default)
_base_parser.add_argument("--log-dir", "-l", help="Directory to write log file to.",
                          default=".")

root_parser = ArgumentParser(parents=[_base_parser], add_help=False)
"""Root `csm_test_utils` parser"""
root_parser.add_argument("--dry", action="store_true",
                         help="Validate test without running")

__sub_parsers = root_parser.add_subparsers(dest="test", required=True, help="Test to be run")


def _subparser(name):
    return __sub_parsers.add_parser(name, add_help=False, parents=[_base_parser])


# AS monitor
AGP_AS_MONITOR = _subparser("as_monitor")
AGP_AS_MONITOR.add_argument("--port", help="port to be listened", default=23456, type=int)

# AS LB
AGP_AS_LB = _subparser("as_load")

# LB monitor
AGP_LB_MONITOR = _subparser("monitor")

# RDS monitor
AGP_RDS_MONITOR = _subparser("rds_monitor")

# SFS
AGP_SFS = _subparser("sfs_compare")
AGP_SFS.add_argument("--mount_point", help="point where NFS mounted", default="/mnt/sfs_share",
                     type=str)

# RDS backup
AGP_RDS_BACKUP = _subparser("rds_backup_monitor")
AGP_RDS_BACKUP.add_argument("--instance_id", help="RDS instance ID")
AGP_RDS_BACKUP.add_argument("--cloud_config", help="Clouds config file")
AGP_RDS_BACKUP.add_argument("--cloud_name", help="Name of cloud")
AGP_RDS_BACKUP.add_argument("--endpoint", help="Endpoint")

# DNS host check
AGP_DNS_HOST_CHECK = _subparser("internal_dns_host_check")
AGP_DNS_HOST_CHECK.add_argument("--dns_name", help="dns name of server to resolve", type=str)

# DNS resolving
AGP_DNS_RESOLVE = _subparser("internal_dns_resolve")
AGP_DNS_RESOLVE.add_argument("--dns_name", help="dns name of server to resolve", type=str)

# LB Rebalance
AGP_REBALANCE = _subparser("rebalance")
AGP_REBALANCE.add_argument("--nodes", type=int, default=None, help="Expected number of nodes")
AGP_REBALANCE.add_argument("--timeout", type=float, default=60.0, help="Rebalance timeout")

# LB Load
AGP_LB_LOAD = _subparser("lb_load")

# RDS backup generate data
AGP_RDS_GENERATE = _subparser("rds_backup_generate_data")
AGP_RDS_GENERATE.add_argument("--run_option", dest="run_option",
                              choices=["pg2", "sqla"])
AGP_RDS_GENERATE.add_argument("--source")
AGP_RDS_GENERATE.add_argument("--host")
AGP_RDS_GENERATE.add_argument("--port")
AGP_RDS_GENERATE.add_argument("--database", "-db", default="entities")
AGP_RDS_GENERATE.add_argument("--username", "-user")
AGP_RDS_GENERATE.add_argument("--password", "-pass")
AGP_RDS_GENERATE.add_argument("--drivername", default="postgresql+psycopg2")

# RDS backup check

AGP_BACKUP_CHECK = _subparser("rds_backup_check")
AGP_BACKUP_CHECK.add_argument("--instance_id", help="RDS instance ID")
AGP_BACKUP_CHECK.add_argument("--cloud_config", help="Clouds config file")
AGP_BACKUP_CHECK.add_argument("--cloud_name", help="Name of cloud")
AGP_BACKUP_CHECK.add_argument("--endpoint", help="Endpoint")
