#!/bin/bash
set -e
# rm -rf back_end/.mypy_cache
# rm -rf back_end/__pycache__
# rm -rf front_end/.mypy_cache
# rm -rf front_end/__pycache__
# rm -rf front_end/pf2
# scp -r * mgashler@jacquard.ddns.uark.edu:/var/www/autograder/
scp back_end/*.py mgashler@jacquard.ddns.uark.edu:/var/www/autograder/back_end/
