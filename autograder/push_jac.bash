#!/bin/bash
set -e
rm -rf back_end/.mypy_cache
rm -rf back_end/__pycache__
scp -r * mgashler@jacquard.ddns.uark.edu:/var/www/banana_quest/
