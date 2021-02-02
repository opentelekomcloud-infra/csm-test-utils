import unittest

from csm_test_utils.__main__ import ENTRY_POINTS, main


class TestMain(unittest.TestCase):
    def test_main(self):
        for test in ENTRY_POINTS:
            with self.subTest(test):
                main(["--dry", test])

    def test_invalid(self):
        with self.assertRaisesRegex(SystemExit, "2"):
            main(["--dry", "asdsd"])


if __name__ == "__main__":
    unittest.main()
