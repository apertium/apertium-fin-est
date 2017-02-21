#!/usr/bin/python -w
# -*- coding: utf8 -*-

import sys

if __name__ == "__main__":
    if len(sys.argv)!=3:
        sys.exit(1)
    dic = open(sys.argv[1], "r")
    ol = dic.readline()
    while ol:
        if "</section>" in ol:
            sys.stdout.write("\n\n\n    <!-- SECTION: "+sys.argv[2]+" -->\n\n")
            nl = sys.stdin.readline()
            while nl:
                sys.stdout.write(nl)
                nl = sys.stdin.readline()
            sys.stdout.write(ol)
        else:
            sys.stdout.write(ol)
        ol = dic.readline()

