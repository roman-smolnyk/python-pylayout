#!/usr/bin/env bash
git push origin master
git push origin_github master

git tag -a v0.1.2 -m "v0.1.2"
git push origin v0.1.2
git push origin_github v0.1.2

python -m build
python -m twine upload dist/*
rm -rf dist

