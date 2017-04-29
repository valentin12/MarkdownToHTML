#!/usr/bin/python3
from parser.gfm import GFMParser

p = GFMParser()
p.parse_text("""\tfoo\tbaz\t\tbim
""")
print(p.get_html())
