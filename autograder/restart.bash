#!/bin/bash
set -e
echo stopping...
sudo systemctl stop autograder.service
echo removing stdout and stderr...
rm -f stdout.txt
rm -f stderr.txt
echo restarting...
sudo systemctl start autograder.service
echo done
