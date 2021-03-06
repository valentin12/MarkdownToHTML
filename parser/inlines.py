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

import re
import string
import html


class InlineParser(object):
    @staticmethod
    def parse(input_string):
        parts = [Text(input_string)]
        parts = InlineParser.compute(InlineParser.get_autolinks, [], parts)
        parts = InlineParser.compute(InlineParser.get_emailautolinks, [Autolink], parts)
        parts = InlineParser.compute(InlineParser.get_code_spans, [Autolink, EMailAutolink], parts)
        parts = InlineParser.compute(InlineParser.get_emphasis, [CodeSpan, Autolink, EMailAutolink], parts)
        parts = InlineParser.compute(InlineParser.get_hard_breaks, [CodeSpan, Autolink, EMailAutolink], parts)
        parts = InlineParser.compute(InlineParser.unescape, [CodeSpan, Autolink, EMailAutolink], parts)
        return "".join([e.get_html() for e in parts])

    @staticmethod
    def compute(function, exceptions, parts):
        out = []
        for part in parts:
            if type(part) is Text:
                out.extend(function(part.text))
            else:
                part.compute(function, exceptions)
                out.append(part)
        return out


    @staticmethod
    def look_for_link_or_img():
        # TODO: not supported yet
        pass

    @staticmethod
    def get_autolinks(text):
        autolink = re.compile("[\s\S]*?<(?P<link>(?P<scheme>[a-zA-Z][a-zA-Z+-.]+?):[^\s<>]*?)>")
        pos = 0
        parts = []
        while pos < len(text):
            m = autolink.match(text, pos)
            if m is not None:
                r = m.groupdict()
                if pos != m.start("link") - 1:
                    # Save text before link
                    parts.append(Text(text[pos:m.start("link") - 1]))
                parts.append(Autolink())
                parts[-1].add(Text(r['link']))
                pos = m.end()
            else:
                parts.append(Text(text[pos:]))
                break
        return parts

    @staticmethod
    def get_emailautolinks(text):
        autolink = re.compile("[\s\S]*?<(?P<address>[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*)>")
        pos = 0
        parts = []
        while pos < len(text):
            m = autolink.match(text, pos)
            if m is not None:
                r = m.groupdict()
                if pos != m.start("address") - 1:
                    # Save text before link
                    parts.append(Text(text[pos:m.start("address") - 1]))
                parts.append(EMailAutolink())
                parts[-1].add(Text(r['address']))
                pos = m.end()
            else:
                parts.append(Text(text[pos:]))
                break
        return parts

    @staticmethod
    def get_code_spans(text):
        """Get code spans"""
        code = re.compile(r"[\s\S]*?(?=[^`]|\A)(?P<tick>`+)(?!`)(?P<content>[\s\S]*?)(?<=[^`])\1((?!`)|$)")
        pos = 0
        parts = []
        while pos < len(text):
            m = code.match(text, pos)
            if m is not None:
                r = m.groupdict()
                if pos != m.start('tick'):
                    parts.append(Text(text[pos:m.start('tick')]))
                parts.append(CodeSpan())
                parts[-1].add(Text(r['content']))
                pos = m.end()
            else:
                parts.append(Text(text[pos:]))
                break
        return parts

    @staticmethod
    def get_hard_breaks(text):
        hard_break = re.compile(r"[\s\S]*?(?P<break>[ ]{2,}|\t|[\\])\n")
        pos = 0
        parts = []
        if pos == len(text):
            return [Text(text)]
        while pos < len(text):
            m = hard_break.match(text, pos)
            if m is not None:
                parts.append(Text(text[pos:m.start("break")].rstrip()))
                parts.append(HardBreak())
                pos = m.end()
            else:
                parts.append(Text(text[pos:]))
                break
        return parts

    @staticmethod
    def unescape(text):
        return [Text(re.sub(r"\\(?P<char>[{}])".format(re.escape(string.punctuation)), r"\g<char>", text))]

    @staticmethod
    def get_emphasis(text):
        """Get emphasis"""
        delimiter_stack = []
        delimiter_regex = re.compile(r"[\s\S]*?(?P<pre>[^_*\s\]!\[]?)(?P<deli>[*]+|[_]+|\[|!\[|])(?P<post>\S?)")
        pos = 0
        parts = []
        while True:
            m = delimiter_regex.match(text, pos)
            if m is not None:
                parts.append(Text(text[pos:m.end("deli")]))
                r = m.groupdict()
                if m.group("deli").startswith("*"):
                    delimiter_stack.append(Delimiter("*", len(m.group("deli")), not r['pre'] and r['post'],
                                                     r['pre'],
                                                     len(parts) - 1))
                elif m.group("deli").startswith("_"):
                    delimiter_stack.append(Delimiter("_", len(m.group("deli")),
                                                     (not r['pre'] or r['pre'] in string.punctuation) and r['post'],
                                                     r['pre'], len(parts) - 1))
                elif m.group("deli") == "[":
                    delimiter_stack.append(Delimiter("[", 1, True, True, len(parts) - 1))
                elif m.group("deli") == "![":
                    delimiter_stack.append(Delimiter("![", 1, True, True, len(parts) - 1))
                else:
                    InlineParser.look_for_link_or_img()
                pos = m.end("deli")
            else:
                parts.append(Text(text[pos:]))
                break
        emphs = InlineParser.process_emphasis(delimiter_stack, None)
        used = []
        out = []
        for e in emphs:
            parts[e[0].position].text = parts[e[0].position].text[:-e[2]]
            text = ""
            for i in range(e[0].position + 1, e[1].position):
                used.append(i)
                text += parts[i].text
            text += parts[e[1].position].text[:-e[2]]
            used.append(e[1].position)
            out.append((Emphasis(strong=e[2] > 1), e[0].position + 1))
            out[-1][0].add(Text(text))
        for i, part in enumerate(parts):
            if i not in used:
                out.append((parts[i], i))
        return [e[0] for e in sorted(out, key=lambda x: x[1])]

    @staticmethod
    def process_emphasis(delimiter_stack, stack_bottom):
        emphs = []
        delimiter_stack = delimiter_stack
        if stack_bottom is None:
            current_position = 0
        else:
            current_position = stack_bottom + 1
        
        while current_position < len(delimiter_stack):
            cur_del = delimiter_stack[current_position]
            if cur_del.type not in ["*", "_"] or not cur_del.active or not cur_del.potential_closer:
                current_position += 1
                continue
            i = current_position - 1
            while i > -1:
                other = delimiter_stack[i]
                if other.type != cur_del.type or not other.active or not other.potential_opener:
                    i -= 1
                    continue
                else:
                    if cur_del.number >= 2 and other.number >= 2:
                        # start, end, size
                        emphs.append((other, cur_del, 2))
                        cur_del.number -= 2
                        other.number -= 2
                    else:
                        emphs.append((other, cur_del, 1))
                        cur_del.number -= 1
                        other.number -= 1
                    for e in delimiter_stack:
                        if other.position <= e.position <= cur_del.position:
                            e.active = False
                    break
            current_position += 1
        return emphs


class Delimiter(object):
    def __init__(self, type, number, potential_opener, potential_closer, position):
        self.type = type
        self.number = number
        self.potential_opener = potential_opener
        self.potential_closer = potential_closer
        self.active = True
        self.position = position


class Inline(object):
    _TEMPLATE = ""

    def __init__(self):
        self.children = []

    def get_html(self):
        return self._TEMPLATE

    def add(self, inline):
        self.children.append(inline)

    def compute(self, function, exceptions):
        if type(self) in exceptions:
            return
        temp = []
        for child in self.children:
            if type(child) is Text:
                temp.extend(function(child.text))
            else:
                child.compute(function, exceptions)
                temp.append(child)
        self.children = temp


class SoftBreak(Inline):
    _TEMPLATE = "\n"


class HardBreak(Inline):
    _TEMPLATE = "<br />"
    def get_html(self):
        return self._TEMPLATE


class Emphasis(Inline):
    _TEMPLATE_EM = "<em>{content}</em>"
    _TEMPLATE_STRONG = "<strong>{content}</strong>"

    def __init__(self, strong=False):
        super().__init__()
        self.strong = strong

    def get_html(self):
        if not self.children:
            return ""
        if self.strong:
            return self._TEMPLATE_STRONG.format(content="".join([c.get_html() for c in self.children]))
        else:
            return self._TEMPLATE_EM.format(content="".join([c.get_html() for c in self.children]))


class Text(Inline):
    def __init__(self, text=""):
        super().__init__()
        self.text = text

    def get_html(self):
        return html.escape(self.text)


class CodeSpan(Inline):
    _TEMPLATE = "<code>{content}</code>"

    def get_html(self):
        return self._TEMPLATE.format(content=html.escape("".join([c.get_html() for c in self.children])).strip())


class Autolink(Inline):
    _TEMPLATE = "<a href=\"{link}\">{text}</a>"
    def get_html(self):
        text = self.children[0].get_html()
        return self._TEMPLATE.format(link=text, text=text)


class EMailAutolink(Inline):
    _TEMPLATE = "<a href=\"mailto:{link}\">{text}</a>"

    def get_html(self):
        text = self.children[0].get_html()
        return self._TEMPLATE.format(link=text, text=text)