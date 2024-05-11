#!/bin/bash
# pyinstaller main.py --onefile
pyinstaller main.spec
rm -r 312831014
mkdir 312831014
cp main.py dist/main readme.txt makefile 312831014
tar cvf 312831014.tar 312831014
rm -r dist build