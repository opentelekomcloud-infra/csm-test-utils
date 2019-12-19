from csm_test_utils.autoscaling import main as as_main
from csm_test_utils.common import root_parser
from csm_test_utils.continuous import main as c_main
from csm_test_utils.continuous_entities import main as rds_main
from csm_test_utils.rebalance_test import main as r_main

args = root_parser.parse_args()
if args.test == "monitor":
    c_main()
if args.test == "rebalance":
    r_main(60)
if args.test == "rds_monitor":
    rds_main()
if args.test == "as_monitor":
    as_main()
