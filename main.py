#!/usr/bin/python3
from parser.gfm import GFMParser

p = GFMParser()
p.parse_text("-   \n  foo\n")
print(p.get_html())
