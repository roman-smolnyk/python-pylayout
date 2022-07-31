import os
import sys
from os.path import dirname as up

path = up(up(os.path.abspath(__file__)))
sys.path.append(path)

from src.pylayout import Layout


def test():
    layout = Layout()
    print(layout.get())
    layout.set("uk")
    print(layout.list())
    print(layout.detect_language("ё"))
    print(layout.translate("ghbdsn", "en", "uk"))
    print(layout.get())


if __name__ == "__main__":
    test()
