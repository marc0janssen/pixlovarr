#!/bin/sh

cmdpath=`echo $1 | sed 's/ //g' | sed 's/\//_/g'`

#write output of cronjob to dockerlog
(printf "%s : " "$(date "+%F %T")";echo "$1";$1) &> /proc/1/fd/1
