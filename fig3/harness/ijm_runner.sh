# Parallel runner for Fiji macros only (light CPU); claims a line by adding it to done.txt before running.
FJ=<work>/fiji/Fiji
while true; do
  line=$(grep -vxF -f done.txt queue.txt | grep ' ijm$' | head -1)
  if [ -z "$line" ]; then sleep 30; continue; fi
  echo "$line" >> done.txt
  set -- $line; d=$1; task=$2
  (cd $d && timeout 1800 xvfb-run -a $FJ/fiji-linux-x64 -batch macro.ijm > run.log 2>&1)
  python3 score_task.py $d $task >> scores.log 2>&1
done
