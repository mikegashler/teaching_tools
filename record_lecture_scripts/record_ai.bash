#!/bin/bash
set -e -x

# Find a suitable filename
d=`date +%Y-%m-%d`
fn=""
for a in {a..z}; do
	fn=tmp/vid/ai/${d}${a}.ogv
	if [ ! -f ${fn} ]; then
		break;
	fi
done

#recordmydesktop --device hw:0,0 -o ${fn}
recordmydesktop -x=1380 -y=0 --width=1000 --height=750 --device hw:0,0 --on-the-fly-encoding -o ${fn}

scp ${fn} $box6:/var/www/html/ai/
