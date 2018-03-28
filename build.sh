#!/usr/bin/env bash
version=0.0.30
rm lib/*.pyc
python2 -m py_compile lib/*.py
fulldir=$PWD
dir=${PWD##*/}
cd ..
zip -r $dir/$dir.$version.zip $dir -i \*.py \*.pyc \*.xml **/icon.png **/LICENSE.txt -x .vscode/**\* .git/**\* -x $dir/.vscode/**\* $dir/.git/**\*
cd $fulldir
