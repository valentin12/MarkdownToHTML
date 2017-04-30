#!/usr/bin/python3
from parser.gfm import GFMParser
from parser.inlines import InlineParser

p = GFMParser()
p.parse_text("""The number of windows in my house is
14.  The number of doors is 6.
""")
print(p.get_html())

# print(InlineParser.parse("*Hallo* **fett**"))
