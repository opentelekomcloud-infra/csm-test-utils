from csm_test_utils.autoscaling import as_lb_main, as_wh_main
from csm_test_utils.common import root_parser
from csm_test_utils.continuous import main as c_main
from csm_test_utils.continuous_entities import main as rds_main
from csm_test_utils.files_rotation import main as sfs_main
from csm_test_utils.rebalance_test import main as r_main
from csm_test_utils.dns import dns_lookup_main, host_main
from csm_test_utils.rds import rds_backup_main

args = root_parser.parse_args()
if args.test == "monitor":
    c_main()
if args.test == "rebalance":
    r_main(60)
if args.test == "rds_monitor":
    rds_main()
if args.test == "as_monitor":
    as_wh_main()
if args.test == "as_load":
    as_lb_main()
if args.test == "sfs_compare":
    sfs_main()
if args.test == "internal_dns_resolve":
    dns_lookup_main()
if args.test == "internal_dns_host_check":
    host_main()
if args.test == "rds_backup_monitor":
    rds_backup_main()
