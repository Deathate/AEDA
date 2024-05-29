import os
import sys


class StopExecution(Exception):
    def _render_traceback_(self):
        return []


def exit():
    raise StopExecution


class HiddenPrints:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout
