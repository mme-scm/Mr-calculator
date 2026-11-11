#!/bin/sh
PY="/home/user/venv_sage/bin/python -W ignore"
cd /home/user/Mr-calculator
until ! pgrep -f "run_pass.py tw3 tw 12 12" > /dev/null; do sleep 10; done
$PY scripts/run_pass.py tw3 tw 12 12 kinds=pd kmin=3 kmax=3 procs=4 skip_conventions=1 nocomposite=1 budget=2400
echo PASSES_DONE
