# Sequential CPU queue: each line of queue.txt is "<dir> <task> <kind>" (kind = py | ijm). Processes new lines as they appear.
CP=<work2>/cpenv/bin/python
FJ=<work>/fiji/Fiji
touch queue.txt done.txt
while true; do
  line=$(grep -vxF -f done.txt queue.txt | head -1)
  if [ -z "$line" ]; then sleep 15; continue; fi
  set -- $line; d=$1; task=$2; kind=$3
  if [ "$kind" = py ]; then (cd $d && timeout 3600 $CP script.py > run.log 2>&1)
  else (cd $d && timeout 1800 xvfb-run -a $FJ/fiji-linux-x64 -batch macro.ijm > run.log 2>&1); fi
  python3 score_task.py $d $task >> scores.log 2>&1
  echo "$line" >> done.txt
done
