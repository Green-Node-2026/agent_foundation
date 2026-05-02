from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class ColorTextTestResult(unittest.TextTestResult):
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    RESET = "\033[0m"

    def addSuccess(self, test):
        super().addSuccess(test)
        self.stream.writeln(f"{self.GREEN}PASS{self.RESET} {test}")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.stream.writeln(f"{self.RED}FAIL{self.RESET} {test}")

    def addError(self, test, err):
        super().addError(test, err)
        self.stream.writeln(f"{self.YELLOW}ERROR{self.RESET} {test}")


class ColorTextTestRunner(unittest.TextTestRunner):
    resultclass = ColorTextTestResult


if __name__ == "__main__":
    loader = unittest.defaultTestLoader
    suite = loader.discover("tests")
    runner = ColorTextTestRunner(verbosity=2)
    raise SystemExit(0 if runner.run(suite).wasSuccessful() else 1)
