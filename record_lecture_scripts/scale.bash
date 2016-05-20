#!/bin/bash
set -e
for file in *
do
	fn=$(basename "$file")
	ext="${fn##*.}"
	name="${fn%.*}"
	if [ ! ${name:0:5} == "small" ]; then

		# Make the target filename
		if [ "$ext" == "mp4" ] || [ "$ext" == "ogv" ]; then
			targext=${ext}
		elif [ "$ext" == "MTS" ]; then
			targext="mp4"
		else
			targext="skip"
		fi
		targ="small${name}.${targext}"

		# Scale down the video
		if [ ! -f $targ ] && [ ! "$targext" == "skip" ]; then
			avconv -i $file -s 480x360 -strict experimental $targ
		fi
	fi
done

