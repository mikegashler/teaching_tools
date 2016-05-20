#!/bin/bash
set -e # exit if any errors occur

# Check that we received a file
if [ $# -eq 0 ]; then echo "No file submitted"; exit; fi
filename=$(basename "$1")
echo "Received file: $filename"

# Unzip it into a folder owned by the "sandbox" user
cd $(dirname $1)
mkdir -p sandbox
chmod 777 sandbox
cd sandbox
extension="${filename##*.}"
echo "File type: $extension"
echo "Extracting..."
if [ "$extension" = "zip" ]; then
	echo "unzip $filename"
	sudo -u sandbox unzip $1 | tail -n +2
elif [ "$extension" = "gz" ]; then
	echo "tar xzf $filename"
	sudo -u sandbox tar xzf $1
elif [ "$extension" = "tgz" ]; then
	echo "tar xzf $filename"
	sudo -u sandbox tar xzf $1
elif [ "$extension" = "7z" ]; then
	echo "7za x $filename"
	sudo -u sandbox 7za x $1
else
	echo "tar xjf $filename"
	sudo -u sandbox tar xjf $1
fi

# Touch all the files (to prevent "clock skew" build issues)
find . -exec touch {} \;

# Change into the folder with the build script, and make sure it is named "build_and_run.bash"
if [ ! -f build_and_run.bash ]; then
	if [ -f build_and_run.bat ]; then sudo -u sandbox cp build_and_run.bat build_and_run.bash; else
		if [ -f build.bash ]; then sudo -u sandbox cp build.bash build_and_run.bash; else
			if [ -f build.bat ]; then sudo -u sandbox cp build.bat build_and_run.bash; else
				declare d1=($(find -name build_and_run.bash))
				if [ ! -z "$d1" ]; then cd $(dirname $d1); else
					declare d2=($(find -name build_and_run.bat))
					if [ ! -z "$d2" ]; then
						cd $(dirname $d2);
						sudo -u sandbox cp build_and_run.bat build_and_run.bash
					else
						declare d3=($(find -name build.bash))
						if [ ! -z "$d3" ]; then
							cd $(dirname $d3);
							sudo -u sandbox cp build.bash build_and_run.bash
						else
							declare d4=($(find -name build.bat))
							if [ ! -z "$d4" ]; then
								cd $(dirname $d4);
								sudo -u sandbox cp build.bat build_and_run.bash
							fi
						fi
					fi
				fi
			fi
		fi
	fi
fi

# Make sure the 
if [ ! -f build_and_run.bash ]; then echo "No build script was found! Expected to find a file named build_and_run.bash or build_and_run.bat"; exit; fi
sudo -u sandbox chmod 755 ./build_and_run.bash
sudo -u sandbox dos2unix -q ./build_and_run.bash

# Print the names of all the files in the current folder (just to give the user some idea of what folder it is in)
echo ""
echo "Listing files in the current folder..."
ls -1
echo ""

# Launch the "build_and_run.bash" script
echo "Launching the script..."
sudo -u sandbox ./build_and_run.bash &

# Start a time-out timer
CHILD_PID=$!
TIME_LIMIT=300
for (( i = 0; i < $TIME_LIMIT; i++ )); do
	sleep 1

	#proc=$(ps -ef | awk -v pid=$CHILD_PID '$2==pid{print}{}')
	#if [[ -z "$proc" ]]; then
	#	break
	#fi

	if ! ps -p $CHILD_PID > /dev/null; then
		break
	fi
done
if [ $i -lt $TIME_LIMIT ]; then
	echo "Process terminated."
else
	echo "!!! Time limit exceeded! Killing the unfinished process !!!"
	kill -HUP $CHILD_PID
	kill -9 $CHILD_PID
fi
cd ..
if [ -d "obj" ]; then
	rm -rf obj
	rm -rf lib
fi
