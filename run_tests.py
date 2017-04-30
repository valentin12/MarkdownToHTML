#!/usr/bin/python3
from parser.gfm import GFMParser
import sys

# Read file from standard input and print result
parser = GFMParser()
for line in sys.stdin:
    parser.parse_line(line)
print(parser.get_html())
