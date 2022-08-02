import json
import os
import re
import subprocess
import sys

if "win32" in sys.platform:
    import ctypes
    import win32api

    # from ctypes import wintypes

from ._lang_layouts import LAYOUTS


class Layout:

    _ubuntu_call = "gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell --method org.gnome.Shell.Eval '{command}'"
    _windows_call = "chcp 65001 >NUL & powershell {command}"

    def __init__(self) -> None:
        if "win32" not in sys.platform and "linux" not in sys.platform:
            raise TypeError("Invalid system")

        self.cached_layouts = None

        try:
            sys.stdin.reconfigure(encoding="utf-8")
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except:
            pass

    def get(self) -> str:
        """Return current layout as 'ru', 'us' etc"""
        if "win32" in sys.platform:
            if not self.cached_layouts:
                self.cached_layouts = self._get_available()
            w = ctypes.windll.user32.GetForegroundWindow()
            tid = ctypes.windll.user32.GetWindowThreadProcessId(w, 0)
            result = ctypes.windll.user32.GetKeyboardLayout(tid)

            layouts = {v: k for k, v in self.cached_layouts.items()}
            layout = layouts[result]
            # dictionary[new_key] = dictionary.pop(old_key)
        elif "linux" in sys.platform:
            get_current_layout_command = "imports.ui.status.keyboard.getInputSourceManager().currentSource.id"
            command = self._ubuntu_call.format(command=get_current_layout_command)
            result = self._subprocess_execute(command)
            layout = re.findall('"(.*)"', result)[0]
            # Convert names

        layout = "en" if layout == "us" else layout
        layout = "uk" if layout == "ua" else layout
        return layout

    def set(self, dest_lang: str) -> bool:
        """dest_lang: 'ru', 'us' etc"""
        if not self.cached_layouts:
            self.cached_layouts = self._get_available()
        if "win32" in sys.platform:
            # Cache result to speed up

            # w = ctypes.windll.user32.GetForegroundWindow()
            # tid = ctypes.windll.user32.GetWindowThreadProcessId(w, 0)
            # result = ctypes.windll.user32.GetKeyboardLayout(tid)
            # z = self.available()
            # lid = int(z["uk"]) & (2**16 - 1)
            # lid_hex = hex(lid)
            # Needs HKL
            win32api.PostMessage(ctypes.windll.user32.GetForegroundWindow(), 0x0050, 2, self.cached_layouts[dest_lang])

            # ActivateKeyboardLayout = ctypes.windll.user32.ActivateKeyboardLayout
            # ActivateKeyboardLayout.argtypes = (wintypes.HKL, wintypes.UINT)
            # ActivateKeyboardLayout.restype = wintypes.HKL
            # ActivateKeyboardLayout(self.available()[dest_lang], 0)
        elif "linux" in sys.platform:
            set_layout_command = f"imports.ui.status.keyboard.getInputSourceManager().inputSources[{self.cached_layouts[dest_lang]}].activate()"
            command = self._ubuntu_call.format(command=set_layout_command)
            result = self._subprocess_execute(command)
            return True

    def list(self) -> list:
        """Return list of available layouts"""
        return list(self._get_available().keys())

    @staticmethod
    def translate(text: str, source_lang: str, dest_lang: str) -> str:
        """Convert qwerty into йцукен or reverse"""
        converted = ""
        find = LAYOUTS[source_lang]
        take = LAYOUTS[dest_lang]
        for char in text:
            index = find.find(char)
            converted += char if index < 0 else take[index]
        return converted

    @staticmethod
    def detect_language(text: str) -> str:
        """Return 'uk', 'en' etc"""
        indexes = {}
        for char in text:
            for key, value in LAYOUTS.items():
                index = value.find(char)
                if index >= 0:
                    indexes[key] = indexes.get(key, 0) + 1

        language = (None, 0)
        for key, value in indexes.items():
            if value > language[1]:
                language = (key, value)
        return language[0]

    # def _available_mapped(self):
    #     if "win32" not in sys.platform:
    #         return
    #     # Converts KLID into HKL
    #     layouts = self._get_available()

    def _get_available(self) -> dict:
        layouts = {}
        if "win32" in sys.platform:
            # returns KLID
            command = self._windows_call.format(command="Get-WinUserLanguageList")
            result = self._subprocess_execute(command, shell=True)
            all_data = result.strip().split("\r\n\r")
            for data in all_data:
                line = data.split("\r\n")
                for l in line:
                    pair = l.split(" : ")
                    if "LanguageTag" in pair[0]:
                        key = pair[1].strip().lower()[-2:]
                    elif "InputMethodTips" in pair[0]:
                        layouts[key] = pair[1].strip().replace("{", "").replace("}", "")
                        break
            # l = ctypes.windll.user32.GetKeyboardLayout(0)
            # z = gw.getActiveWindow()
            # titles = gw.getAllTitles()
            # win = gw.getWindowsWithTitle(titles[2])[0]
            # win.activate()
            # l2 = ctypes.windll.user32.GetKeyboardLayout(0)
            # z._hWnd

            # Convert KLID into HKL
            for k, v in layouts.copy().items():
                win32api.LoadKeyboardLayout(v.split(":")[1], 1)
                layouts[k] = win32api.GetKeyboardLayout(0)
                win32api.LoadKeyboardLayout("00000409", 1)
        elif "linux" in sys.platform:
            get_layouts_command = "imports.ui.status.keyboard.getInputSourceManager().inputSources"
            command = self._ubuntu_call.format(command=get_layouts_command)
            result = self._subprocess_execute(command)
            result_dict = json.loads(re.findall(r"\{.*\}", result)[0])
            for key, value in result_dict.items():
                layouts[value["id"]] = int(key)

        if "us" in layouts:
            layouts["en"] = layouts.pop("us")
        if "ua" in layouts:
            layouts["uk"] = layouts.pop("ua")
        return layouts

    def _subprocess_execute(self, command, shell=False):
        if isinstance(command, str):
            command = command.split()
        process = subprocess.Popen(command, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, _ = process.communicate()
        return output.decode()
