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
elif [ "$extension" = "tar" ]; then
	echo "tar xf $filename"
	sudo -u sandbox tar xf $1
elif [ "$extension" = "7z" ]; then
	echo "7za x $filename"
	sudo -u sandbox 7za x $1
else
	echo "tar xjf $filename"
	sudo -u sandbox tar xjf $1
fi

# Touch all the files (to prevent "clock skew" build issues)
find . -exec touch {} \;

# Rename folders with spaces in them to use underscores instead
find . -depth -name "* *" -execdir rename 's/ /_/g' "{}" \;

# Find the build script and change into its folder, and make sure it is named "build.bash"
declare d1=($(find -name build.bash))
if [ ! -z "$d1" ]; then
	cd $(dirname $d1);
else
	declare d2=($(find -name build.bat))
	if [ ! -z "$d2" ]; then
		cd $(dirname $d2);
		sudo -u sandbox cp build.bat build.bash
	fi
fi

# Make sure the script was found
if [ ! -f build.bash ]; then
	echo "No build script was found! Expected to find a file named build.bash or build.bat"
	exit
fi

# Make sure the build script and is executable
sudo -u sandbox chmod 755 ./build.bash

# Make sure the build script has unix line endings
sudo -u sandbox dos2unix -q ./build.bash

# Print the names of all the files in the current folder
echo ""
echo "Listing files in the current folder..."
ls -1
echo ""

# Launch the "build.bash" script (in a separate thread)
echo "Launching the script..."
sudo -u sandbox ./build.bash &

# Start a time-out timer
CHILD_PID=$!
TIME_LIMIT=120
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
	echo "Finished."
else
	echo "!!! Time limit exceeded! Killing the unfinished process !!!"
	kill -HUP $CHILD_PID
	kill -9 $CHILD_PID
fi

# Clean up some generated files
cd ..
if [ -d "obj" ]; then
	find . -name "*.class"  -exec -exec rm {} \;
	find . -name "*.o"  -exec -exec rm {} \;
	find . -name "*.obj"  -exec -exec rm {} \;
	find . -name "*.ncb"  -exec -exec rm {} \;
	find . -name "*.suo"  -exec -exec rm {} \;
	find . -name "*.pch"  -exec -exec rm {} \;
	find . -name "*.lib"  -exec -exec rm {} \;
	find . -name "*.a"  -exec -exec rm {} \;
	find . -name "__MACOSX"  -exec -exec rm -rf {} \;
	find . -name ".git"  -exec -exec rm -rf {} \;
	find . -name ".settings"  -exec -exec rm -rf {} \;
fi
