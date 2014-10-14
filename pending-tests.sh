#!/bin/bash

C=2
GREP='.'
if [ $# -eq 1 ]
then
    C=$1
    GREP='WORKS'
fi

bash wiki-tests.sh Pending fin est update | grep -C $C "$GREP"

bash wiki-tests.sh Pending est fin update | grep -C $C "$GREP"
