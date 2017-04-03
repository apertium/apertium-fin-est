#!/bin/bash

ll="fin-est" 
lr="est-fin" 
l1="textbook/soome" 
l2="textbook/eesti" 
t1="udt/udtfin2" 
t2="udt/udtest2" 
rul1=$l1".tolge"
rul2=$t1".tolge"

# assume test.sh and testudt.sh have run successfully already

# run udt dix&rules on textbook
# append textbook generated dix to default 
cat $rul2"1.dix" | sort | uniq | python di.py dix/apertium-fin-est.fin-est.dix "generated from udt 1"  > dix/apertium-fin-est.fin-est1.udt.dix 

# compile apertium-fin-est system with dix1
cp -f dix/apertium-fin-est.fin-est1.udt.dix ../../apertium-fin-est.fin-est.dix
cd ../..
make
cd dev/lexind

#run with dix1 - enhanced by textbook development set, compare with default

./rls.sh $ll $l1 $l2 $rul2"1.rul" "3"

# run again with new dix&rules
# append  
cat $rul1"-ls3.dix" | sort | uniq | python di.py dix/apertium-fin-est.fin-est1.udt.dix "generated from textbook 3"  > dix/apertium-fin-est.fin-est3.ub.dix 

# compile 
cp -f dix/apertium-fin-est.fin-est3.ub.dix ../../apertium-fin-est.fin-est.dix
cd ../..
make
cd dev/lexind
#run, compare with ls2
./rls.sh $ll $l1 $l2 $rul1"-ls3.rul" "4"

#runboth on testset, compare with each other, ls1 & ls2
x1="testset/udtfin"
x2="testset/udtest"
rul3=$x1".tolge"

./rls.sh $ll $x1 $x2 $rul1"-ls3.rul" "3"


# run testbook dix&rules on udt
# append textbook generated dix to default 
cat $rul1"1.dix" | sort | uniq | python di.py dix/apertium-fin-est.fin-est.dix "generated from textbook 1"  > dix/apertium-fin-est.fin-est1.dix 

# compile apertium-fin-est system with dix1
cp -f dix/apertium-fin-est.fin-est1.dix ../../apertium-fin-est.fin-est.dix
cd ../..
make
cd dev/lexind

#run with dix1 - enhanced by textbook development set, compare with default

./rls.sh $ll $t1 $t2 $rul1"1.rul" "3"

# run again with new dix&rules
# append 
cat $rul2"-ls3.dix" | sort | uniq | python di.py dix/apertium-fin-est.fin-est1.dix "generated from udt 3"  > dix/apertium-fin-est.fin-est3.bu.dix 

# compile 
cp -f dix/apertium-fin-est.fin-est3.bu.dix ../../apertium-fin-est.fin-est.dix
cd ../..
make
cd dev/lexind
# run, compare with ls2
./rls.sh $ll $t1 $t2 $rul2"-ls3.rul" "4"


#runboth on testset, compare with each other, ls1 & ls2
./rls.sh $ll $x1 $x2 $rul2"-ls3.rul" "4"

# append self
cat $rul3"-ls4.dix" | sort | uniq | python di.py dix/apertium-fin-est.fin-est3.bu.dix "generated from test 4"  > dix/apertium-fin-est.fin-est3.4test.dix 

# compile 
cp -f dix/apertium-fin-est.fin-est3.4test.dix ../../apertium-fin-est.fin-est.dix
cd ../..
make
cd dev/lexind
# run, compare with ls3-4, ls2
./rls.sh $ll $x1 $x2 $rul3"-ls4.rul" "5"


# restore initial files in the main folder
cp -f ../../apertium-fin-est.fin-est_default.dix ../../apertium-fin-est.fin-est.dix
cp -f ../../fin-est.rlx_default.bin ../../fin-est.rlx.bin
cp -f ../../est-fin.rlx_default.bin ../../est-fin.rlx.bin


