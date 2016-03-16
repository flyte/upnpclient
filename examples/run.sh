#!/bin/sh

usage () {
    echo "Usage: $0 <example.py>" >&2
    exit 1
}

[ $# -lt 1 ] && usage

export PYTHONPATH=../src/

python $*
