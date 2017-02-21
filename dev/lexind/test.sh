#!/bin/bash

ll="fin-est" 
lr="est-fin" 
l1="textbook/soome" 
l2="textbook/eesti" 
t1="testset/udtfin"
t2="testset/udtest"
rul1=$l1".tolge"
rul2=$t1".tolge"

# additional modes needed to run the tests
cp -f modes/* ../../modes

cp -f ../../fin-est.rlx.bin ../../fin-est.rlx_default.bin
cp -f ../../est-fin.rlx.bin ../../est-fin.rlx_default.bin
cp -f dix/*.bin ../..

touch $rul1.rul
touch $rul2.rul

# prepare morphologically analysed sources and targets
cat $l1.txt | apertium -d ../.. $ll-mrf > $l1.mrf
cat $l2.txt | apertium -d ../.. $lr-mrf > $l2.mrf

cat $t1.txt | apertium -d ../.. $ll-mrf > $t1.mrf
cat $t2.txt | apertium -d ../.. $lr-mrf > $t2.mrf

# compile apertium-fin-est system with dix1
cp -f ../../apertium-fin-est.fin-est.dix ../../apertium-fin-est.fin-est_default.dix

cp -f dix/apertium-fin-est.fin-est.dix ../../apertium-fin-est.fin-est.dix
cd ../..
make
cd dev/lexind

#run with default dix

./r.sh $ll $l1 $l2 $rul1.rul "1"

./r.sh $ll $t1 $t2 $rul1.rul "1"


# append textbook generated dix to default 
cat $rul1"1.dix" | sort | uniq | python di.py dix/apertium-fin-est.fin-est.dix "generated from textbook 1"  > dix/apertium-fin-est.fin-est1.dix 

# compile apertium-fin-est system with dix1
cp -f dix/apertium-fin-est.fin-est1.dix ../../apertium-fin-est.fin-est.dix
cd ../..
make
cd dev/lexind

#run with dix1 - enhanced by development set

./rls.sh $ll $l1 $l2 $rul1"1.rul" "1"

./rls.sh $ll $t1 $t2 $rul1"1.rul" "1"


# append testset generated dix to dix1
cat $rul2"-ls1.dix" | sort | uniq | python di.py dix/apertium-fin-est.fin-est1.dix "generated from testset 1"  > dix/apertium-fin-est.fin-est2.dix 

# compile apertium-fin-est system with dix2
cp -f dix/apertium-fin-est.fin-est2.dix ../../apertium-fin-est.fin-est.dix
cd ../..
make
cd dev/lexind

#run with dix2 - enhanced by development and test set

./rls.sh $ll $l1 $l2 $rul2"-ls1.rul" "2test"

./rls.sh $ll $t1 $t2 $rul2"-ls1.rul" "2test"


# restore initial files in the main folder
cp -f ../../apertium-fin-est.fin-est_default.dix ../../apertium-fin-est.fin-est.dix
cp -f ../../fin-est.rlx_default.bin ../../fin-est.rlx.bin
cp -f ../../est-fin.rlx_default.bin ../../est-fin.rlx.bin


