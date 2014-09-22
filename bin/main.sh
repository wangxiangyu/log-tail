path=$(cd `dirname $0`; pwd)
export PATH="$path/../python2.6.8/bin:$PATH"
echo "[Info] PYTHON : $(which python)"
echo "[Info] PYTHON Version : $(python -V 2>&1)"

cd $path/../src
python main.py
