#!/bin/bash
set -e

folders=$( ls . | grep a1 )
for file in $folders
do
	pushd $file > /dev/null
	echo ""
	echo ""
	echo ""
	declare d1=($(find -name build.bash))
	if [ ! -z "$d1" ]; then
		pushd $(dirname $d1) > /dev/null
		pwd
		./build.bash
		java Game
		popd > /dev/null
	fi
	popd > /dev/null
done
