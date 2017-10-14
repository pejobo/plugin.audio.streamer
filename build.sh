echo $0
rm lib/*.pyc
python2 -m py_compile lib/*.py
cd ..
find plugin.audio.streamer -type f | grep -v ".*vscode.*" | grep -v ".*build.sh" | grep -v ".*test.py.*" | grep -v ".*zip" | zip plugin.audio.streamer.0.0.1.zip -@
cd plugin.audio.streamer
