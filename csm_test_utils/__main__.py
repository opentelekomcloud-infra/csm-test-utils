from importlib import import_module
from inspect import signature

from csm_test_utils.parsers import root_parser

ENTRY_POINTS = {
    "monitor": "csm_test_utils.continuous",
    "rebalance": "csm_test_utils.rebalance_test",
    "rds_monitor": "csm_test_utils.continuous_entities",
    "as_monitor": "csm_test_utils.autoscaling.smn_webhook",
    "as_load": "csm_test_utils.autoscaling.loadbalancer",
    "sfs_compare": "csm_test_utils.files_rotation",
    "internal_dns_resolve": "csm_test_utils.dns.dns_resolving",
    "internal_dns_host_check": "csm_test_utils.dns.host_check",
    "rds_backup_monitor": "csm_test_utils.rds.rds_backup",
    "lb_load": "csm_test_utils.loadbalancer.lb_monitor",
    "rds_backup_generate_data": "csm_test_utils.rds_backup.generation.cli",
    "rds_backup_check": "csm_test_utils.rds_backup.backup_check.rds_backup",
}


def _check_main(_main):
    sig = signature(_main)
    assert not sig.parameters, "main function should accept no arguments"


def main(args=None):
    """Main csm_test_utils entry point"""

    args, _ = root_parser.parse_known_args(args=args)
    import_path = ENTRY_POINTS[args.test]
    module = import_module(import_path)
    main_fnc = getattr(module, "main")
    _check_main(main_fnc)
    if args.dry:
        return
    main_fnc()


if __name__ == "__main__":
    main()
