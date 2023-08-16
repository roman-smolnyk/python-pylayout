#!/usr/bin/env bash
rm -rf dist
python setup.py sdist
python -m twine upload dist/*
