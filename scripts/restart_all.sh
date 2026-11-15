#!/bin/sh
# Starts whatever of the unattended jobs is not running (after a restart of the machine): the stage 7 queue,
# the orchestrator, the targeted-search queue and the memory log.  Safe to run at any time.
# Round 4 of the targeted search (queue_T4) is paused while the flag pause_T4 exists (2026-11-15, user: the
# work on u_Z and u_R comes first); remove the flag and run this script to resume it where it stopped.
cd /home/user/Mr-calculator
up() { pgrep -f "$1" > /dev/null; }
up "scripts/queue_6d.s[h]" || grep -q "^QUEUE_A_DONE" logs/queue_A.log || { nohup setsid sh scripts/queue_6d.sh >> logs/queue_A.log 2>&1 & echo "started queue_6d"; }
up "scripts/orchestrate.s[h]" || [ -f /home/user/mrcalc_scratch/flags/ALL_DONE ] || { nohup setsid bash scripts/orchestrate.sh >> logs/orchestrate.log 2>&1 & echo "started orchestrator"; }
up "scripts/queue_T1.s[h]" || grep -q "^T1_DONE" logs/queue_T1.log 2>/dev/null || { nohup setsid sh scripts/queue_T1.sh >> logs/queue_T1.log 2>&1 & echo "started queue_T1"; }
up "scripts/queue_T2.s[h]" || grep -q "^T2_DONE" logs/queue_T2.log 2>/dev/null || { nohup setsid sh scripts/queue_T2.sh >> logs/queue_T2.log 2>&1 & echo "started queue_T2"; }
up "scripts/queue_T3.s[h]" || grep -q "^T3_DONE" logs/queue_T3.log 2>/dev/null || { nohup setsid sh scripts/queue_T3.sh >> logs/queue_T3.log 2>&1 & echo "started queue_T3"; }
up "scripts/queue_T4.s[h]" || [ -f /home/user/mrcalc_scratch/flags/pause_T4 ] || grep -q "^T4_DONE" logs/queue_T4.log 2>/dev/null || { nohup setsid sh scripts/queue_T4.sh >> logs/queue_T4.log 2>&1 & echo "started queue_T4"; }
up "scripts/queue_U.s[h]" || grep -q "^U_DONE" logs/queue_U.log 2>/dev/null || { nohup setsid sh scripts/queue_U.sh >> logs/queue_U.log 2>&1 & echo "started queue_U"; }
up "scripts/queue_U2.s[h]" || grep -q "^U2_DONE" logs/queue_U2.log 2>/dev/null || { nohup setsid sh scripts/queue_U2.sh >> logs/queue_U2.log 2>&1 & echo "started queue_U2"; }
up "scripts/queue_M46.s[h]" || grep -q "^M46_MOVES_DONE" logs/queue_M46.log 2>/dev/null || { nohup setsid sh scripts/queue_M46.sh >> logs/queue_M46.log 2>&1 & echo "started queue_M46"; }
up "verify_chirality.p[y] check" || grep -q "^CHECK_DONE" /home/user/mrcalc_scratch/repair/chir_main.log 2>/dev/null || { MRCALC_STAGE=/home/user/mrcalc_stage nohup setsid /home/user/venv_sage/bin/python -W ignore scripts/verify_chirality.py check out=/home/user/mrcalc_scratch/repair/chir_main.jsonl procs=3 passes=cc,ccR,ccb,g2cc,g2tw,mu,tw2,tw3,tw3x,tw4,tw4x,tw5,tw5x,tw6,tw6x,twB,twL >> /home/user/mrcalc_scratch/repair/chir_main.log 2>&1 & echo "started chirality check"; }
up "used_avail_M[B]" || { nohup setsid sh -c 'while true; do echo "$(date -u +%m-%d\ %H:%M:%S) used_avail_MB $(free -m | awk "NR==2{print \$3, \$7}") load $(cut -d" " -f1-3 /proc/loadavg) top $(ps -eo rss,comm --sort=-rss | awk "NR>1&&NR<5{printf \"%s:%dMB \", \$2, \$1/1024}")"; sleep 30; done' >> logs/mem.log 2>&1 & echo "started memory log"; }
sleep 1
