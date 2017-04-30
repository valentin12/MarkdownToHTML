#!/usr/bin/python3
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
        while True:
            # One or more blocks may be closed
            line_untabbed = Document.tab_to_spaces(line, -1, 0)
            self.document.close_check(line_untabbed, self.line_number)
            last_open, remainder = self.document.get_last_open(line_untabbed)
            last = self.document.get_last()
            to_strip = len(line_untabbed) - len(remainder)
            remainder = Document.tab_to_spaces(line, to_strip, 0)[to_strip:]
            block = self.document.new_block(last_open, remainder, self.line_number, last, stripped=to_strip)
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
                # # Loose or tight list
                last_list = self.document.get_last_open_types([BulletList, OrderedList])
                if last_list and \
                        (len(last_list.children[-1].children) or last_list.children[-1].start_line < self.line_number):
                    if last_list.loose < 0:
                        last_list.loose = sum([len(c.children) for c in last_list.children])
                    self.document.close_marked()
                    break
            if self.lazy and not remainder.strip() and not type(last_open) in [FencedCodeBlock, IndentedCodeBlock]:
                # Empty continuation line not allowed
                self.document.close_marked()
                break
            if block is not None and type(block) is not ListItem and type(last_open) in [BulletList, OrderedList]:
                # Close list if created block is no list item
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
                # If new block starts, create it and close open
                self.document.close_marked()
                last_open.add(block)
                if not issubclass(type(block), ContainerBlock):
                    break
        self.line_number += 1

    def get_html(self):
        return self.document.get_html()
