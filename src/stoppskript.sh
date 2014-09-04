#!/usr/bin/bash
pidfiles="tm.pid cm.pid mb.pid"

for pidfile in $pidfiles
do
	pid=`tail $pidfile` &&
	kill $pid &&
	rm $pidfile
done
