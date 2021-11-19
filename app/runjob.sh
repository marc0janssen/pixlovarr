#!/bin/sh

# Name: Pixlovarr
# Coder: Marco Janssen (twitter @marc0janssen)
# date: 2021-11-19 18:53:46
# update: 2021-11-19 18:53:54

# cmdpath=`echo $1 | sed 's/ //g' | sed 's/\//_/g'`

#write output of cronjob to dockerlog
(printf "%s : " "$(date "+%F %T")";echo "$1";$1) &> /proc/1/fd/1
