#!/usr/bin/python3
from parser.gfm import GFMParser
from parser.inlines import InlineParser

p = GFMParser()
p.parse_text("""# Feeling fine
I'm all *right* __Jack__ take **your** hands off my `stack`
- Hallo Welt
1. Geht's anders
und
2. als man denkt
* Weisheit
 ``` info
Das geht ab *Heueueue*
```

Was gibt's noch neues

`allo`""")
print(p.get_html())

# print(InlineParser.parse("*Hallo* **fett**"))
