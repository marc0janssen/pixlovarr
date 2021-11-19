#!/bin/sh

cmdpath=`echo $1 | sed 's/ //g' | sed 's/\//_/g'`

(printf "%s : " "$(date "+%F %T")";echo "$1";$1) &> /logs/$cmdpath.log
