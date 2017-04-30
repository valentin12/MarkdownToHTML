#!/usr/bin/python3
"""
Markdown to HTML converter
Copyright (C) 2017 Valentin Pratz <git@valentinpratz.de>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from parser.gfm import GFMParser
import sys

# Read file from standard input and print result
parser = GFMParser()
for line in sys.stdin:
    parser.parse_line(line)
print(parser.get_html())
