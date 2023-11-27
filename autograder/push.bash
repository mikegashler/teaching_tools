#!/bin/bash
set -e
rm -rf back_end/.mypy_cache
rm -rf back_end/__pycache__
scp -r -P33 * mike@gashler.com:/var/www/gashler.com/mike/paradigms/proj5/
