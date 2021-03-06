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

from .blocks import *


class GFMParser():
    def __init__(self):
        self.document = Document()
        self.line_number = 0
        self.last_strip = 0
        self.lazy = False

    def reset(self):
        self.document = Document()
        self.line_number = 0

    def parse_text(self, text):
        lines = text.split("\n")
        lines = [l + "\n" for l in lines[:-1]] + [lines[-1]]
        for line in lines:
            self.parse_line(line)
        return self

    def parse_line(self, line):
        """
        Parse single line in context of previous lines in document
        """
        while True:
            # Convert tabs to spaces for finding block structure
            line_untabbed = Document.tabs_to_spaces(line, -1, 0)
            # One or more blocks may be closed
            self.document.close_check(line_untabbed, self.line_number)
            # Get last open block and the line without indentation
            last_open, remainder = self.document.get_last_open(line_untabbed)
            # Get last, maybe closed, block
            last = self.document.get_last()
            # Calc length of indentation
            to_strip = len(line_untabbed) - len(remainder)
            # Get remainder, but only convert tabs needed as spaces
            remainder = Document.tabs_to_spaces(line, to_strip, 0)[to_strip:]
            # Get a newly started block if there is any
            block = self.document.new_block(last_open, remainder, self.line_number, last, stripped=to_strip)
            # If no indentation is there anymore, the line could be a lazy continuation line
            self.lazy = to_strip == 0 and (self.lazy or self.last_strip > 0)
            self.last_strip = to_strip
            if type(last) is FencedCodeBlock and not last.closed:
                if last.close_next:
                    # Line was for closing fenced code block, don't use it for other things
                    self.document.close_marked()
                else:
                    # Line must belong to fenced code block
                    last.add_line(remainder, to_strip, self.lazy)
                break
            if block is None and not remainder.strip() and \
                    type(last_open) not in [BlockQuote, FencedCodeBlock, IndentedCodeBlock]:
                # Empty line, if it's in a list the list could be loose
                # Find last open list
                last_list = self.document.get_last_open_types([BulletList, OrderedList])
                if last_list and \
                        (len(last_list.children[-1].children) or last_list.children[-1].start_line < self.line_number):
                    if last_list.loose < 0:
                        # List has been tight, set number of current child to indicate point of blank line
                        last_list.loose = sum([len(c.children) for c in last_list.children])
                    self.document.close_marked()
                    break
            if self.lazy and not remainder.strip() and not type(last_open) in [FencedCodeBlock, IndentedCodeBlock]:
                # Empty continuation line not possible -> discard
                self.document.close_marked()
                break
            if block is not None and type(block) is not ListItem and type(last_open) in [BulletList, OrderedList]:
                # Close list if newly created block is no list item
                while type(last_open) in [BulletList, OrderedList]:
                    last_open.close_check(line, self.line_number, force=True)
                    last_open.close_marked()
                    last_open, remainder = self.document.get_last_open(line_untabbed)
                continue
            if block is None or (type(block) is Paragraph and type(last) is Paragraph and not last.closed):
                # Incorporate text into last block
                last.add_line(remainder, to_strip, self.lazy)
                break
            else:
                # new block starts, create it and close open
                self.document.close_marked()
                last_open.add(block)
                if not issubclass(type(block), ContainerBlock):
                    break
        self.line_number += 1

    def get_html(self):
        return self.document.get_html()
