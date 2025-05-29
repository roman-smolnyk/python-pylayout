import json
import logging
import os
import platform
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

if "Windows" in platform.platform():
    import winreg
    import ctypes
    import win32api
    import win32con
    import win32gui
    import win32process

    # from ctypes import wintypes

from ._lang_layouts import LAYOUTS

logger = logging.getLogger(__name__)


def ban_russian_nazi(lang: str):
    if lang == "ru":
        logger.error("Glory to Ukraine!!!")
        sys.exit()


def adapt_lang_codes(key: str, invert=False):
    codes = {"us": "en", "ua": "uk"}
    if invert:
        codes = {v: k for k, v in codes.items()}
    code = codes.get(key)
    return code if code else key


class Layout:
    _ubuntu_call = "gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell --method org.gnome.Shell.Eval '{command}'"
    _windows_call = "chcp 65001 >NUL & powershell {command}"

    def __init__(self, use_cache=True) -> None:
        if "Windows" not in platform.platform() and not "Linux" in platform.platform():
            raise TypeError("Invalid system")

        self.use_cache = use_cache
        self.layouts = None

        try:
            sys.stdin.reconfigure(encoding="utf-8")
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except:
            pass

    def get(self) -> str:
        """Return current layout as 'uk', 'us' etc"""
        if "Windows" in platform.platform():
            if self.use_cache == False or not self.layouts:
                self.layouts = self._get_available_layouts()

            hwnd = win32gui.GetForegroundWindow()
            thread_id, process_id = win32process.GetWindowThreadProcessId(hwnd)
            hkl = win32api.GetKeyboardLayout(thread_id)

            # import pygetwindow

            # for window in pygetwindow.getAllWindows():
            #     if window._hWnd == hwnd:
            #         break
            # else:
            #     raise Exception("No window assosiated with console")

            layouts_reversed = {v: k for k, v in self.layouts.items()}
            layout = layouts_reversed[hkl]

            # klid_1 = hex(hkl & 0xFFFFF)
            # for lang, klid_2 in self.layouts.items():
            #     if klid_1[-4:] == klid_2[-4:]:
            #         layout = lang
            #         break
            # else:
            #     raise Exception("Missing KLID")

            # dictionary[new_key] = dictionary.pop(old_key)
        elif "Linux" in platform.platform():
            get_current_layout_command = "imports.ui.status.keyboard.getInputSourceManager().currentSource.id"
            command = self._ubuntu_call.format(command=get_current_layout_command)
            result = self._subprocess_execute(command)
            if "true" in result:
                layout = re.findall('"(.*)"', result)[0]
            else:
                command = "gsettings get org.gnome.desktop.input-sources mru-sources"
                result = self._subprocess_execute(command)
                pre_result = re.findall(r"\(.*?\)", result)[0]
                layout = re.findall(r"'(.*?)'", pre_result)[1]

        layout = adapt_lang_codes(layout)

        ban_russian_nazi(layout)
        return layout

    def set(self, dest_lang: str) -> bool:
        """dest_lang: 'uk', 'us' etc"""
        ban_russian_nazi(dest_lang)
        if self.use_cache == False or not self.layouts:
            self.layouts = self._get_available_layouts()

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

            # hkl = win32api.LoadKeyboardLayout(self.layouts[dest_lang], win32con.KLF_ACTIVATE)
            code = win32api.PostMessage(
                win32gui.GetForegroundWindow(),
                win32con.WM_INPUTLANGCHANGEREQUEST,
                0,
                self.layouts[dest_lang],
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
            set_layout_command = (
                f"imports.ui.status.keyboard.getInputSourceManager().inputSources[{self.layouts[dest_lang]}].activate()"
            )
            command = self._ubuntu_call.format(command=set_layout_command)
            result = self._subprocess_execute(command)
            if "true" in result:
                return True
            else:
                url = "https://askubuntu.com/questions/1412130/dbus-calls-to-gnome-shell-dont-work-under-ubuntu-22-04"
                logger.warning(f"Check this url and verify if module works: {url}")

                if False:  # It changes layout to desired one but breaks default Ubuntu's functionality
                    command = f"setxkbmap {adapt_lang_codes(dest_lang, invert=True)}"
                    result = self._subprocess_execute(command)
                    if "Error" in result:
                        return False
                    else:
                        return True

    def toggle(self):
        """Cycle through available layouts"""
        if "Windows" in platform.platform():
            win32api.PostMessage(win32gui.GetForegroundWindow(), win32con.WM_INPUTLANGCHANGEREQUEST)

    def list(self) -> list:
        """Return list of available layouts"""
        if self.use_cache == False or not self.layouts:
            self.layouts = self._get_available_layouts()
        # tuple_ = win32api.GetKeyboardLayoutList()
        return list(self.layouts.keys())

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

    def _get_all_layouts(self) -> dict:
        assert "Windows" in platform.platform(), "Windows specific"

        all_layouts = {}

        path = Path(r"SYSTEM\CurrentControlSet\Control\Keyboard Layouts")
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, str(path))
        num_subkeys, num_values, _ = winreg.QueryInfoKey(key)
        for i in range(num_subkeys):
            subkey_name = winreg.EnumKey(key, i)
            subkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, str(path / subkey_name))
            num_subkeys1, num_values1, _ = winreg.QueryInfoKey(subkey)
            value_data, value_type = winreg.QueryValueEx(subkey, "Layout Text")
            all_layouts[subkey_name] = value_data
            # for j in range(num_values1):
            #     value_name, value_data, value_type = winreg.EnumValue(subkey, j)
            #     if value_name == "Layout Text":
            #         all_layouts[subkey_name] = value_data
            #         break
            winreg.CloseKey(subkey)
        winreg.CloseKey(key)

        return all_layouts

    def _get_preffered_layouts(self) -> list:
        assert "Windows" in platform.platform(), "Windows specific"

        preffered_layouts = []

        path = Path(r"Keyboard Layout\Preload")
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, str(path))
        num_subkeys, num_values, _ = winreg.QueryInfoKey(key)

        for i in range(num_values):
            value_name, value_data, value_type = winreg.EnumValue(key, i)
            preffered_layouts.append(value_data)
        winreg.CloseKey(key)

        return preffered_layouts

    def _get_preffered_layouts_with_lang(self) -> dict:
        layouts_klid = {}
        all_layouts = self._get_all_layouts()
        preffered_layouts = self._get_preffered_layouts()
        for klid in preffered_layouts:
            layouts_klid[klid] = all_layouts.get(klid)
        return layouts_klid

    def _get_preffered_layouts_with_lang_2(self) -> dict:
        """This method is slow so previously I used caching"""
        layouts_klid = {}
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
                    key = adapt_lang_codes(key)
                elif "InputMethodTips" in pair[0]:
                    layouts_klid[key] = pair[1].strip().replace("{", "").replace("}", "")
                    break
        return layouts_klid

    def _get_preffered_layouts_with_lang_3(self) -> dict:
        """This registry key can hold irrelevant klid unlike 'Preload' key"""
        layouts_klid = {}
        path = Path(r"Control Panel\International\User Profile")
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, str(path))
        num_subkeys, num_values, _ = winreg.QueryInfoKey(key)

        for i in range(num_subkeys):
            subkey_name = winreg.EnumKey(key, i)
            subkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, str(path / subkey_name))
            value_name, value_data, value_type = winreg.EnumValue(subkey, 2)
            layouts_klid[value_name] = subkey_name.split("-")[0].lower().strip()
            winreg.CloseKey(subkey)
        winreg.CloseKey(key)

        return layouts_klid

    def _get_available_layouts(self) -> dict:
        layouts = {}
        if "Windows" in platform.platform():
            # l = ctypes.windll.user32.GetKeyboardLayout(0)
            # z = gw.getActiveWindow()
            # titles = gw.getAllTitles()
            # win = gw.getWindowsWithTitle(titles[2])[0]
            # win.activate()
            # l2 = ctypes.windll.user32.GetKeyboardLayout(0)
            # z._hWnd

            # Get HKL layout values
            # layouts_hkl = {}
            # while True:
            #     # win32api.LoadKeyboardLayout(v.split(":")[1], win32con.KLF_ACTIVATE)
            #     # win32api.GetKeyboardLayout(0)
            #     # thread_id = ctypes.windll.user32.GetWindowThreadProcessId(win32gui.GetForegroundWindow(), None)

            #     hwnd = win32gui.GetForegroundWindow()
            #     thread_id, process_id = win32process.GetWindowThreadProcessId(hwnd)
            #     hkl = win32api.GetKeyboardLayout(thread_id)
            #     klid = hex(hkl & 0xFFFFF)
            #     # to_hex = hex(hkl)
            #     # to_int = int(to_hex, 16)
            #     if hkl in list(layouts_hkl.keys()):
            #         break
            #     else:
            #         layouts_hkl[hkl] = klid
            #     self.toggle()
            #     time.sleep(0.1)  # Need timeout to change layout

            # Len can differ because there is a bug in Windows that I have 2 ukrainian layouts
            # assert len(layouts_klid) == len(layouts_hkl)

            layouts_ = win32api.GetKeyboardLayoutList()

            layouts_klid = self._get_preffered_layouts_with_lang_3()
            layouts_klid = {v: k for k, v in layouts_klid.items()}
            hkl = win32api.GetKeyboardLayout()  # Get current thread layout
            # Convert KLID into HKL
            for key, value in layouts_klid.items():
                layouts[key] = win32api.LoadKeyboardLayout(value.split(":")[1], win32con.KLF_ACTIVATE)
            # Switch back thread layout
            klid = layouts_klid.get({v: k for k, v in layouts.items()}.get(hkl)).split(":")[1]
            win32api.LoadKeyboardLayout(klid, win32con.KLF_ACTIVATE)

            # # layouts_klid = self._get_preffered_layouts_with_lang_2()
            # # Convert KLID into HKL
            # for hkl in win32api.GetKeyboardLayoutList():
            #     klid1 = hex(hkl & 0xFFFFF)
            #     for lang, klid2 in layouts_klid.items():
            #         hkl2 = win32api.LoadKeyboardLayout(klid2.split(":")[1], win32con.KLF_ACTIVATE)
            #         if klid1[-5:] == klid2[-5:]:
            #             layouts[lang] = hkl
            #             break
            #         # English language is not too precise
            #         elif klid1[-3:] == klid2[-3:] and not layouts.get(lang):
            #             layouts[lang] = hkl
            #             break

            return layouts
        elif "Linux" in platform.platform():
            get_layouts_command = "imports.ui.status.keyboard.getInputSourceManager().inputSources"
            command = self._ubuntu_call.format(command=get_layouts_command)
            result = self._subprocess_execute(command)
            if "true" in result:
                result_dict = json.loads(re.findall(r"\{.*\}", result)[0])
                for key, value in result_dict.items():
                    layouts[value["id"]] = int(key)
                adapted_layouts = {}
                for key, value in layouts.items():
                    key = adapt_lang_codes(key)
                    adapted_layouts[key] = value
                layouts = adapted_layouts
            else:
                command = "gsettings get org.gnome.desktop.input-sources sources"
                result = self._subprocess_execute(command)
                for i in re.findall(r"'(.*?)'", result)[1::2]:
                    i = adapt_lang_codes(i)
                    layouts[i] = i
            return layouts

    def _subprocess_execute(self, command, shell=False):
        if isinstance(command, list):
            pass
        elif isinstance(command, str):
            command = shlex.split(command)
        process = subprocess.Popen(command, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, _ = process.communicate()
        return output.decode()
