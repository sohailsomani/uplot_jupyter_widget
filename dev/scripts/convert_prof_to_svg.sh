#!/bin/bash

input="$1"
output="${input/.prof/.svg}"

if [ "$input" == "" ]; then
    echo "Usage: $0 inputfile"
    exit 1
fi;

gprof2dot --format=pstats "$input" | dot -Tsvg > "$output"

echo "Saved to $output"
