#!/usr/bin/env bash
python setup.py sdist
python -m twine upload dist/*
