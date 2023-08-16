import json
import os
import platform
import re
import shlex
import subprocess
import sys
import time

if "Windows" in platform.platform():
    import ctypes
    import win32api
    import win32con
    import win32gui
    import win32process

    # from ctypes import wintypes

from ._lang_layouts import LAYOUTS


def ban_ruscists(lang: str):
    if lang == "ru":
        print("Glory to Ukraine!!!")
        sys.exit()


class Layout:
    _ubuntu_call = "gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell --method org.gnome.Shell.Eval '{command}'"
    _windows_call = "chcp 65001 >NUL & powershell {command}"

    def __init__(self) -> None:
        if "Windows" not in platform.platform() and not "Linux" in platform.platform():
            raise TypeError("Invalid system")

        self.cached_layouts = None

        try:
            sys.stdin.reconfigure(encoding="utf-8")
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except:
            pass

    def get(self) -> str:
        """Return current layout as 'uk', 'us' etc"""
        if "Windows" in platform.platform():
            if not self.cached_layouts:
                self.cached_layouts = self._get_available()

            # Using ctypes as it probably faster but I'm not sure
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            tid = ctypes.windll.user32.GetWindowThreadProcessId(hwnd, 0)
            result = ctypes.windll.user32.GetKeyboardLayout(tid)

            layouts = {v: k for k, v in self.cached_layouts.items()}
            layout = layouts[result]
            # dictionary[new_key] = dictionary.pop(old_key)
        elif "Linux" in platform.platform():
            get_current_layout_command = "imports.ui.status.keyboard.getInputSourceManager().currentSource.id"
            command = self._ubuntu_call.format(command=get_current_layout_command)
            result = self._subprocess_execute(command)
            layout = re.findall('"(.*)"', result)[0]

        # Convert lang names
        layout = "en" if layout == "us" else layout
        layout = "uk" if layout == "ua" else layout

        ban_ruscists(layout)
        return layout

    def set(self, dest_lang: str) -> bool:
        """dest_lang: 'uk', 'us' etc"""
        ban_ruscists(dest_lang)
        if not self.cached_layouts:
            self.cached_layouts = self._get_available()
        if "Windows" in platform.platform():
            # Cache result to speed up

            # w = ctypes.windll.user32.GetForegroundWindow()
            # tid = ctypes.windll.user32.GetWindowThreadProcessId(w, 0)
            # result = ctypes.windll.user32.GetKeyboardLayout(tid)
            # z = self.available()
            # lid = int(z["uk"]) & (2**16 - 1)
            # lid_hex = hex(lid)
            # Needs HKL
            # win32api.PostMessage(ctypes.windll.user32.GetForegroundWindow(), 0x0050, 2, self.cached_layouts[dest_lang])
            code = win32api.PostMessage(
                win32gui.GetForegroundWindow(),
                win32con.WM_INPUTLANGCHANGEREQUEST,
                0,
                self.cached_layouts[dest_lang],
            )
            if not code:
                return True
            else:
                return False

            # ActivateKeyboardLayout = ctypes.windll.user32.ActivateKeyboardLayout
            # ActivateKeyboardLayout.argtypes = (wintypes.HKL, wintypes.UINT)
            # ActivateKeyboardLayout.restype = wintypes.HKL
            # ActivateKeyboardLayout(self.available()[dest_lang], 0)
        elif "Linux" in platform.platform():
            set_layout_command = f"imports.ui.status.keyboard.getInputSourceManager().inputSources[{self.cached_layouts[dest_lang]}].activate()"
            command = self._ubuntu_call.format(command=set_layout_command)
            result = self._subprocess_execute(command)
            # TODO Analyze result for success
            return True

    def toggle(self):
        """Cycle through available layouts"""
        if "Windows" in platform.platform():
            win32api.PostMessage(win32gui.GetForegroundWindow(), win32con.WM_INPUTLANGCHANGEREQUEST)

    def list(self) -> list:
        """Return list of available layouts"""
        if not self.cached_layouts:
            self.cached_layouts = self._get_available()
        # tuple_ = win32api.GetKeyboardLayoutList()
        return list(self.cached_layouts.keys())

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
        if "Windows" in platform.platform():
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
            for i in range(len(layouts.items())):
                # win32api.LoadKeyboardLayout(v.split(":")[1], win32con.KLF_ACTIVATE)
                # win32api.GetKeyboardLayout(0)
                # thread_id = ctypes.windll.user32.GetWindowThreadProcessId(win32gui.GetForegroundWindow(), None)
                thread_id, process_id = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())
                hkl = win32api.GetKeyboardLayout(thread_id)
                klid = hex(hkl & 0xFFFFF)
                # to_hex = hex(hkl)
                # to_int = int(to_hex, 16)
                for k, v in layouts.copy().items():
                    if isinstance(v, str) and klid[-4:] == v.split(":")[0]:
                        layouts[k] = hkl
                        break
                self.toggle()
                time.sleep(0.1)  # Need timeout to change layout
            pass
        elif "Linux" in platform.platform():
            get_layouts_command = "imports.ui.status.keyboard.getInputSourceManager().inputSources"
            command = self._ubuntu_call.format(command=get_layouts_command)
            result = self._subprocess_execute(command)
            result_dict = json.loads(re.findall(r"\{.*\}", result)[0])
            for key, value in result_dict.items():
                layouts[value["id"]] = int(key)
            pass

        # Convert lang names and persist order
        adapted_layouts = {}
        for key, value in layouts.items():
            key = "en" if key == "us" else key
            key = "uk" if key == "ua" else key
            adapted_layouts[key] = value

        return adapted_layouts

    def _subprocess_execute(self, command, shell=False):
        if isinstance(command, list):
            pass
        elif isinstance(command, str):
            command = shlex.split(command)
        process = subprocess.Popen(command, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, _ = process.communicate()
        return output.decode()
