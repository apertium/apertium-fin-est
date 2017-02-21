#!/bin/bash

cp $4 soome.tolge.nrl

cat $2.txt | apertium -d ../.. $1-biltrans-ls > $2.biltr-ls

cat $2.txt | apertium -d ../.. $1-ls > $2.tolge-ls

cat $2.txt | apertium -d ../.. $1-postchunk-ls  > $2.pchnk-ls


python comp.py $2.txt $3.txt $2.tolge-ls $2.biltr-ls $2.mrf $3.mrf $2.pchnk-ls $4 $5
