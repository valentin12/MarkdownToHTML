#!/usr/bin/python3
from parser.gfm import GFMParser

p = GFMParser()
p.parse_text("- one\n\n two\n")
print(p.get_html())
