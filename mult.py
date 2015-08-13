#!/usr/bin/python -w
# -*- coding: utf8 -*-

# splits multiword bidix entries to separate units, otherwise correct form of the main word will not be generated 
# word order may be more complicated, it's first approximation; apply after chunker (.t1x)

import sys

for line in sys.stdin:
    l = line.strip()
    if l.find("__") > 0:
        words = l.split()
        for i in xrange(len(words)):
            word = words[i]
            if word.find("__") > 0:
                if word.find("<vblex>") > 0: # main word (last) is verb
                    # ex:  ^v<SV>{^aru__saama<vblex><pers><prs><ind><p3><sg>$}$
                    if word.find("<ind>") > 0 or word.find("<imprt>") > 0 or word.find("<neg") > 0: # finite verb form (add also cond, quot)
                        parts = word.split("__")
                        pref = parts[0].split("{^")[0] + "{^"
                        parts[0] = parts[0].split("{^")[1]
                        words[i] = pref + parts[-1]
                        for j in xrange(len(parts)-1):
                            words[i] += " ^a<ADV>{^" + parts[j] + "<adv>$}$" # mostly not adverb, but we don't need to change it
                    else: # infinite verb form
                        parts = word.split("__")
                        pref = parts[0].split("{^")[0] + "{^"
                        parts[0] = parts[0].split("{^")[1]
                        words[i] = ""
                        for j in xrange(len(parts)-1):
                            words[i] += "^a<ADV>{^" + parts[j] + "<adv>$}$ " # mostly not adverb, but we don't need to change it
                        words[i] += pref + parts[-1]
                else: # main word is not verb
                    parts = word.split("__")
                    pref = parts[0].split("{^")[0] + "{^"
                    parts[0] = parts[0].split("{^")[1]
                    words[i] = ""
                    for j in xrange(len(parts)-1):
                        words[i] += "^a<ADV>{^" + parts[j] + "<adv>$}$ " # mostly not adverb, but we don't need to change it
                    words[i] += pref + parts[-1]
        sent = ""
        for word in words:
            sent += word + " "
        print sent
    else:
        print l
