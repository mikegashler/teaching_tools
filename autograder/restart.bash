#!/bin/bash
set -e
echo stopping...
sudo systemctl stop banana_quest.service
echo removing stdout and stderr...
rm -f stdout.txt
rm -f stderr.txt
echo restarting...
sudo systemctl start banana_quest.service
echo done
