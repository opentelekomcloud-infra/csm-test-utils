from ..common import base_parser, sub_parsers

AGP = sub_parsers.add_parser("lb_load", add_help=False, parents=[base_parser])

def main():
    print("1")


if __name__ == "__main__":
    main()
