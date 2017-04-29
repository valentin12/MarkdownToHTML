#!/usr/bin/python3
import re
from .elements import *


class GFMParser():
    def __init__(self):
        self.document = Document()
        self.line_number = 0

    def reset(self):
        self.document = Document()
        self.line_number = 0

    def parse_text(self, text):
        lines = text.split("\n")
        lines = [l + "\n" for l in lines[:-1]] + [lines[-1]]
        for line in lines:
            self.parse_line(line)

    def parse_line(self, line):
        while True:
            # One or more blocks may be closed
            self.document.close_check(line, self.line_number)
            last, remainder = self.document.get_last_open(line)
            block = self.document.new_block(remainder, last, self.line_number)
            if block is None:
                # Incorporate text into last open block
                last.add_line(remainder)
                break
            else:
                # If new block starts, create it and close open
                self.document.close_marked()
                last.add(block)
                if not issubclass(type(block), ContainerBlock):
                    break
        self.line_number += 1

    def get_html(self):
        return self.document.get_html()
