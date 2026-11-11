#!/bin/sh
# final sequence: milestone 7 (upsilon, resumable), re-solve with ablation, export, independent check, tests
PY="/home/user/venv_sage/bin/python -W ignore"
cd /home/user/Mr-calculator
until grep -q "PASSES_DONE" logs/chain_last.log 2>/dev/null; do sleep 10; done
$PY scripts/run_upsilon.py 30 60 > logs/upsilon_final.log 2>&1
$PY scripts/solve.py upsilon ablation > logs/solve_final.log 2>&1
echo SOLVE_EXIT $? >> logs/solve_final.log
/home/user/venv_sage/bin/python checker/check.py export > logs/check_final.log 2>&1
echo CHECK_EXIT $? >> logs/check_final.log
$PY -m pytest tests -q -x > logs/pytest_final.log 2>&1
echo PYTEST_EXIT $? >> logs/pytest_final.log
echo FINALIZE_DONE > logs/finalize.flag
