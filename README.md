# pylayout

`pylayout` is a Python module for getting and setting the current keyboard layout in Windows. It also includes utilities for detecting the language of input characters and translating text between keyboard layouts.

It supports Windows and linux systems.

## Installation

```bash
pip install pylayout
```

## Usage

```python
from pylayout import Layout

layout = Layout(use_cache=False) # use_cache=True reduces calls to the system to acquire list of available layouts speeding up module
print("Current layout:", layout.get())
print("Available layouts:", layout.list())
layout.set("uk") # Set layout to Ukrainian
print("New layout:", layout.get())

# Currently translate and detect_language support only us and uk languages. Can be extended by modifying LAYOUTS dict
char = "ї"
print(f"Language for '{char}':", layout.detect_language(char))
print("Translate 'ghbdsn' from 'en' to 'uk':", layout.translate("ghbdsn", "en", "uk"))
```

## Features

- Get the current keyboard layout
- Set the keyboard layout by language code (e.g., `en`, `uk`)
- List all available keyboard layouts
- Detect the language associated with a given character
- Translate text from one keyboard layout to another (e.g., fix "ghbdsn" typed in the wrong layout)

## Fixes

There are some issues on windows so here are some resources to fix them

- <https://superuser.com/questions/1360623/cant-remove-unneeded-keyboard-layouts-no-such-setting-anywhere>
- <https://superuser.com/questions/957552/how-to-delete-a-keyboard-layout-in-windows-10/1340511#1340511>
