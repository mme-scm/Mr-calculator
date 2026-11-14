#!/bin/sh
# Starts whatever of the unattended jobs is not running (after a restart of the machine): the stage 7 queue,
# the orchestrator, the targeted-search queue and the memory log.  Safe to run at any time.
cd /home/user/Mr-calculator
up() { pgrep -f "$1" > /dev/null; }
up "scripts/queue_6d.s[h]" || grep -q "^QUEUE_A_DONE" logs/queue_A.log || { nohup setsid sh scripts/queue_6d.sh >> logs/queue_A.log 2>&1 & echo "started queue_6d"; }
up "scripts/orchestrate.s[h]" || [ -f /home/user/mrcalc_scratch/flags/ALL_DONE ] || { nohup setsid bash scripts/orchestrate.sh >> logs/orchestrate.log 2>&1 & echo "started orchestrator"; }
up "scripts/queue_T1.s[h]" || grep -q "^T1_DONE" logs/queue_T1.log 2>/dev/null || { nohup setsid sh scripts/queue_T1.sh >> logs/queue_T1.log 2>&1 & echo "started queue_T1"; }
up "scripts/queue_T2.s[h]" || grep -q "^T2_DONE" logs/queue_T2.log 2>/dev/null || { nohup setsid sh scripts/queue_T2.sh >> logs/queue_T2.log 2>&1 & echo "started queue_T2"; }
up "scripts/queue_T3.s[h]" || grep -q "^T3_DONE" logs/queue_T3.log 2>/dev/null || { nohup setsid sh scripts/queue_T3.sh >> logs/queue_T3.log 2>&1 & echo "started queue_T3"; }
up "used_avail_M[B]" || { nohup setsid sh -c 'while true; do echo "$(date -u +%m-%d\ %H:%M:%S) used_avail_MB $(free -m | awk "NR==2{print \$3, \$7}") load $(cut -d" " -f1-3 /proc/loadavg) top $(ps -eo rss,comm --sort=-rss | awk "NR>1&&NR<5{printf \"%s:%dMB \", \$2, \$1/1024}")"; sleep 30; done' >> logs/mem.log 2>&1 & echo "started memory log"; }
sleep 1
