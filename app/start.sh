#!/bin/ash

# Start the first process
/usr/bin/python3 /app/pixlovarr.py &
  
# Start the second process
crond -l 2 -f &
  
# Wait for any process to exit
wait -n
  
# Exit with status of process that exited first
exit $?