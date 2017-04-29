#!/usr/bin/python3
from parser.gfm import GFMParser
import sys
import re

parser = GFMParser()
for line in sys.stdin:
    parser.parse_line(line)
print(parser.get_html())