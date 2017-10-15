#!/usr/bin/env bash
rm lib/*.pyc
python2 -m py_compile lib/*.py
cd ..
find plugin.audio.streamer -type f | grep -v ".git.*" | grep -v ".vscode.*" | grep -v "build.sh" | grep -v "test.py.*" | zip plugin.audio.streamer.0.0.1.zip -@
cd plugin.audio.streamer
