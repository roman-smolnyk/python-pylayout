import os
import sys
import time
from os.path import dirname as up

path = up(up(os.path.abspath(__file__)))
sys.path.append(path)

from src.pylayout import Layout


def test():
    layout = Layout()
    lang = layout.get()
    print("Initial layout:", lang)
    print("Layout after initialization:", layout.get())
    print("List of languages:", layout.list())
    print("Set lang to 'uk':", layout.set("uk"))
    print("Detect language for 'ї':", layout.detect_language("ї"))
    print("Translate 'ghbdsn' from 'en' to 'uk':", layout.translate("ghbdsn", "en", "uk"))
    lang1 = layout.get()
    print("Current layout:", lang1)
    assert lang == "uk" or lang != lang1, "Languages are the same"
    print(f"Set lang to {lang}:", layout.set(lang))
    time.sleep(0.1)
    lang2 = layout.get()
    print("Current layout:", lang2)
    assert lang == lang2, "Languages are differ"


if __name__ == "__main__":
    test()
