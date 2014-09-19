export PATH="$(pwd)/python2.6.8/bin:$PATH"
export PYTHONPATH="$(pwd):$(pwd)/python2.6.8:$(pwd)/vmonitor-tail/"
echo "[Info] PYTHON : $(which python)"
echo "[Info] PYTHON Version : $(python -V 2>&1)"
echo "[Info] PYTHONPATH : $PYTHONPATH"

cd frame/src/
python main.py
