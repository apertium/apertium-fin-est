#!/bin/bash

cat $2.txt | apertium -d ../.. $1-biltrans > $2.biltr

cat $2.txt | apertium -d ../.. $1 > $2.tolge

cat $2.txt | apertium -d ../.. $1-postchunk  > $2.pchnk

python comp.py $2.txt $3.txt $2.tolge $2.biltr $2.mrf $3.mrf $2.pchnk $4 $5
