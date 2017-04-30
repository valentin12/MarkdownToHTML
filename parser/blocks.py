#!/usr/bin/python3
import re
from .inlines import InlineParser


class Block(object):
    """Interface for all Markdown elements"""
    _TEMPLATE = ""
    REGEX = re.compile("")
    _END_REGEX = ""
    START_REGEX = re.compile("")

    def __init__(self):
        self.closed = False
        self.close_next = False
        self.lines = []
        self.children = []

    @classmethod
    def starts(cls, last_open, line, line_number, last):
        return cls.START_REGEX.match(line) is not None

    @classmethod
    def create(cls, line, line_number, stripped):
        return cls()

    def get_html(self):
        return self._TEMPLATE.format(**self.__dict__)

    def get_end_regex(self):
        return re.compile(self._END_REGEX)

    def close_check(self, line, line_number, force=False):
        pass

    def strip_line(self, line):
        return line

    def add_line(self, line, stripped, lazy=False):
        self.lines.append(line)

    def get_last_open(self, line):
        cur_line = self.strip_line(line)
        line = cur_line
        last = self
        for child in self.children:
            if not (child.closed or child.close_next):
                last, line = child.get_last_open(cur_line)
        return last, line

    def get_last_open_types(self, block_types):
        ret = self if type(self) in block_types and not (self.closed or self.close_next) else None
        for child in self.children:
            if not child.closed or child.close_next:
                block = child.get_last_open_types(block_types)
                ret = block if block is not None else ret
        return ret

    def get_last(self):
        return self if not self.children else self.children[-1].get_last()

    def close_marked(self):
        if self.close_next:
            self.closed = True
        for child in self.children:
            if not child.closed:
                child.close_marked()


class LeafBlock(Block):
    def close_check(self, line, line_number, force=False):
        self.close_next = True
        return line

    def get_html(self):
        lines = self.lines
        while lines and not lines[-1].strip():
            lines = lines[:-1]
        return self._TEMPLATE.format(content=InlineParser.parse("".join(lines)), **self.__dict__)


# Leaf blocks
class ThematicBreak(LeafBlock):
    _TEMPLATE = "<hr />"
    START_REGEX = re.compile(r"^ {0,3}([*\-_])[ \t]*(\1[ \t]*){2,}(\1|[ \t])*\n?$")

    def get_html(self):
        return self._TEMPLATE


class ATXHeading(LeafBlock):
    _TEMPLATE = "<h{number}>{content}</h{number}>\n"
    REGEX = re.compile(r"^ {0,3}(?P<number>[#]{1,6})([ \t]|$)(?P<content>.*?(?:(\\#)*))[ \t]*(?:[#]{2,})? *\n?$")
    START_REGEX = re.compile(r"^ {0,3}(?P<number>[#]{1,6})([ \t]|$)")

    def __init__(self, number=1):
        super().__init__()
        self.number = number

    @classmethod
    def create(cls, line, line_number, stripped=0):
        m = cls.REGEX.match(line)
        r = m.groupdict()
        instance = cls(len(r['number']))
        instance.add_line(r['content'], stripped + m.start(2))
        return instance


class SetextHeading(LeafBlock):
    _TEMPLATE = "<h{number}>{content}</{number}>"
    REGEX = re.compile(r"^ {0,3}([=\-])\1* *\n?$")
    START_REGEX = REGEX


class IndentedCodeBlock(LeafBlock):
    _TEMPLATE = "<pre><code>{content}</code></pre>"
    START_REGEX = re.compile(r"^([ ]{4}|[ ]*\t)\s*\S")
    _END_REGEX = r"^ {0,3}\S+"

    @classmethod
    def starts(cls, last_open, line, line_number, last):
        return IndentedCodeBlock.START_REGEX.match(line) is not None \
                and not type(last_open) is Paragraph and not (type(last) is Paragraph and not last.closed) \
                and not ListItem.starts(last_open, line, line_number, last)

    @classmethod
    def create(cls, line, line_number, stripped=0):
        instance = cls()
        instance.add_line(line, stripped)
        return instance

    def add_line(self, line, stripped=0, lazy=False):
        line = Document.tab_to_spaces(line, 4, stripped)
        if line.strip() or len(line) > 4:
            self.lines.append(line[4:])
        else:
            self.lines.append(line.strip(" \t", ))

    def close_check(self, line, line_number, force=False):
        self.close_next = re.compile(self._END_REGEX).match(line) is not None or force

    def get_html(self):
        lines = self.lines
        while lines and not lines[-1].strip():
            lines = lines[:-1]
        return self._TEMPLATE.format(content="".join(lines), **self.__dict__)


class FencedCodeBlock(LeafBlock):
    _TEMPLATE = "<pre><code{class_str}>{content}</code></pre>\n"
    REGEX = re.compile(
        r"^(?P<indentation>[ ]{0,3})(?P<fence>(?P<character>[`~])\3{2,})[ \t]*(?P<info>[^\`]*?)?[ \t]*\n?$")
    _END_REGEX = r"^[ ]{{0,3}}[{character}]{{{number},}} *\n?$"
    START_REGEX = REGEX

    def __init__(self, character, indentation, number, info):
        super().__init__()
        self.character = character
        self.indentation = indentation
        self.number = number
        self.info = info
        self.class_str = ""
        if self.info:
            self.class_str = ' class="language-{}"'.format(self.info.split()[0])

    @classmethod
    def create(cls, line, line_number, stripped):
        r = cls.REGEX.match(line).groupdict()
        return cls(r['character'], len(r['indentation']), len(r['fence']), r['info'])

    def close_check(self, line, line_number, force=False):
        self.close_next = self.get_end_regex().match(line) is not None
        self.closed = self.closed or force

    def get_end_regex(self):
        return re.compile(self._END_REGEX.format(**self.__dict__))

    def add_line(self, line, stripped, lazy=False):
        line = Document.tab_to_spaces(line, self.indentation, stripped)
        if all(c == " " for c in line[:self.indentation]):
            self.lines.append(line[self.indentation:])
        else:
            self.lines.append(line.lstrip(" "))

    def get_html(self):
        return self._TEMPLATE.format(content="".join(self.lines), class_str=self.class_str)


class HTMLBlock(LeafBlock):
    _TEMPLATE = "{content}"


class LinkReferenceDefinition(LeafBlock):
    _TEMPLATE = "<p><a href=\"{url}\" title=\"{title}\">{content}</a></p>"

    def __init__(self, content, url, title):
        super().__init__()
        self.content = content
        self.url = url
        self.title = title


class Paragraph(LeafBlock):
    _TEMPLATE = "<p>{content}</p>\n"
    START_REGEX = re.compile(r"[\s]*\S+")

    def __init__(self):
        super().__init__()
        self.setextheading = False

    @classmethod
    def create(cls, line, line_number, stripped):
        instance = cls()
        instance.add_line(line, stripped)
        return instance
    
    @classmethod
    def starts(cls, last_open, line, line_number, last):
        return type(last_open) is not Paragraph and Paragraph.START_REGEX.match(line)

    def close_check(self, line, line_number, force=False):
        self.close_next = not line.strip() or force
        if (ThematicBreak.START_REGEX.match(line) is not None and SetextHeading.START_REGEX.match(line) is None) \
                or ATXHeading.START_REGEX.match(line) is not None \
                or FencedCodeBlock.START_REGEX.match(line) is not None \
                or BlockQuote.START_REGEX.match(line) is not None \
                or BulletList.START_REGEX.match(line) is not None \
                or (OrderedList.START_REGEX.match(line) is not None and line.startswith("1.") or line.startswith("1)")):
            self.close_next = True

    def add_line(self, line, stripped, lazy=False):
        if SetextHeading.starts(None, line, 0, None) and self.lines and not lazy:
            self.closed = True
            self.setextheading = True
            self.lines.append(line)
        elif not line.strip():
            self.closed = True
        else:
            self.lines.append(line.strip(" \t"))

    def get_html(self):
        if self.setextheading:
            return "<h{number}>{content}</h{number}>\n".format(number=1 if "=" in self.lines[-1] else 2,
                                                               content=InlineParser.parse("".join(self.lines[:-1]).strip()))
        else:
            return self._TEMPLATE.format(content=InlineParser.parse("".join(self.lines).strip()))


# Container blocks
class ContainerBlock(Block):
    _TEMPLATE = "{content}"
    _INNER_TEMPLATE = "{content}"

    def __init__(self):
        super().__init__()
        self.children = []

    def get_html(self):
        children_strings = [self._INNER_TEMPLATE.format(content=child.get_html())
                            for child in self.children]
        return self._TEMPLATE.format(content="".join(children_strings), **self.__dict__)

    def add(self, element):
        self.children.append(element)

    def close_check(self, line, line_number, force=False):
        self.close_next = self.get_end_regex().match(line) is not None or force
        line = self.strip_line(line)
        for child in self.children:
            if not child.closed:
                child.close_check(line, line_number, force=self.close_next)


class BlockQuote(ContainerBlock):
    _TEMPLATE = "<blockquote>\n{content}</blockquote>\n"
    REGEX = re.compile(r"^ {0,3}\>[ ]?(?P<content>.*\n?)$")
    START_REGEX = re.compile(r"^ {0,3}\>")
    _END_REGEX = re.compile(r"^(?! {0,3}\>)")

    def strip_line(self, line):
        return self.REGEX.match(line).groupdict()['content'] if self.REGEX.match(line) else line


class ListItem(ContainerBlock):
    _TEMPLATE = "<li>{content}</li>\n"
    _NEWLINE_TEMPLATE = "<li>\n{content}\n</li>\n"
    REGEX = re.compile(r"^(?P<indentation>[ ]*(([\d]{1,9}[.)])|[\-+*])[ \t]*)(?P<content>.*\n?)$")
    _END_REGEX = r"^[ ]{{0,{indentation}}}\S.*"

    def __init__(self,indentation, start_line):
        super().__init__()
        self.indentation = max(indentation, 2)
        self.start_line = start_line

    @classmethod
    def starts(cls, last_open, line, line_number, last):
        return (type(last_open) is BulletList or type(last_open) is OrderedList) \
                                                 and ListItem.REGEX.match(line)

    @classmethod
    def create(cls, line, line_number, stripped):
        m = cls.REGEX.match(line)
        r = m.groupdict()
        if r['content'] and r['content'].strip():
            indentation = Document.tab_to_spaces(r['indentation'], -1, stripped + m.start(1))
        else:
            indentation = Document.tab_to_spaces(r['indentation'], -1, stripped + m.start(1)).rstrip() + " "
        whitespaces = re.compile(r".*?(?P<whitespaces>[ ]{5,})\n?$").match(indentation)
        if whitespaces is not None:
            indentation = indentation[:whitespaces.start(1) + 1]
        return cls(len(indentation), line_number)

    def close_check(self, line, line_number, force=False):
        self.close_next = self.get_end_regex().match(line) and not line_number == self.start_line or force
        for child in self.children:
            if not child.closed:
                child.close_check(self.strip_line(line), line_number, force=self.close_next)

    def strip_line(self, line):
        if line.find("\n") > -1:
            return line[min(self.indentation, line.find("\n")):]
        else:
            return line[self.indentation:]

    def get_end_regex(self):
        return re.compile(self._END_REGEX.format(indentation=self.indentation - 1))

    def get_html(self, loose=False):
        content = ""
        for child in self.children:
            if not loose and type(child) is Paragraph:
                content += "".join(child.lines).strip()
            else:
                content += child.get_html()
        if loose:
            return self._NEWLINE_TEMPLATE.format(content=content.strip())
        return self._TEMPLATE.format(content=content.strip())


class List(ContainerBlock):
    def __init__(self, indentation):
        super().__init__()
        self.indentation = indentation
        self.loose = -1

    @classmethod
    def starts(cls, last_open, line, line_number, last):
        return cls.START_REGEX.match(line) is not None and not ListItem.starts(last_open, line, line_number, None)

    def strip_line(self, line):
        return line[self.indentation:]

    def get_html(self):
        content = ""
        for child in self.children:
            content += child.get_html(loose=self.is_loose())
        return self._TEMPLATE.format(content=content, **self.__dict__)

    def close_check(self, line, line_number, force=False):
        self.close_next = self.get_end_regex().match(line) is not None \
                          or ThematicBreak.starts(None, line, line_number, None) \
                          or force
        for child in self.children:
            if not child.closed:
                child.close_check(self.strip_line(line), line_number, force=self.close_next)

    def is_loose(self):
        loose = -1 < self.loose < sum([len(c.children) for c in self.children])
        for child in self.children:
            for l in child.children:
                if issubclass(type(l), List):
                    if l.loose > -1 and not l.is_loose() and l is not self.children[-1].children[-1]:
                        # Empty line at end of list
                        return True
        return loose


class OrderedList(List):
    _TEMPLATE = "<ol{start}>\n{content}\n</ol>\n"
    START_REGEX = re.compile(r"^(?P<indentation>[ ]{0,3})(?P<start>[\d]{1,9})(?P<marker>[.)])([ \t]|$)")
    _END_REGEX = r"^(?!([\d]{{1,9}}[{marker}])|(?![ ]{{0,{indentation}}}\S.*))"
    _ALT_END_REGEX = r"^(?![\d]{{1,9}}[{marker}]|\s$|[ \t])"

    def __init__(self, indentation, start, marker):
        super().__init__(indentation)
        self.start_num = start
        self.start = " start=\"{start}\"".format(start=start) if start != 1 else ""
        self.marker = marker
        self.indentation = indentation

    @classmethod
    def starts(cls, last_open, line, line_number, last):
        return cls.START_REGEX.match(line) is not None \
               and not ListItem.starts(last_open, line, line_number, None) \
               and not (type(last_open) is Paragraph and cls.START_REGEX.match(line).groupdict()['start'] != 1)

    @classmethod
    def create(cls, line, line_number, stripped):
        m = cls.START_REGEX.match(line)
        r = m.groupdict()
        instance = cls(len(r['indentation']), int(r['start']), r['marker'])
        instance.add(ListItem.create(instance.strip_line(line), line_number, stripped + instance.indentation))
        return instance

    def get_end_regex(self):
        if self.indentation > 0:
            return re.compile(self._END_REGEX.format(indentation=self.indentation - 1, marker=re.escape(self.marker)))
        else:
            return re.compile(self._ALT_END_REGEX.format(marker=re.escape(self.marker)))


class BulletList(List):
    _TEMPLATE = "<ul>\n{content}</ul>\n"
    START_REGEX = re.compile(r"^(?P<indentation>[ ]{0,3})(?P<marker>[\-+*])([ \t]|$)")
    _END_REGEX = r"^([ ]{{0,{indentation}}}\S.*|[ ]{{{indentation}}}[^{marker}^\s])"
    _ALT_END_REGEX = r"^([^{marker}^\s]|[{marker}]\S)"

    def __init__(self, indentation, marker):
        super().__init__(indentation)
        self.marker = marker
        self.indentation = indentation

    @classmethod
    def create(cls, line, line_number, stripped):
        m = cls.START_REGEX.match(line)
        r = m.groupdict()
        instance = cls(len(r['indentation']), r['marker'])
        instance.add(ListItem.create(instance.strip_line(line), line_number, stripped + instance.indentation))
        return instance

    def get_end_regex(self):
        if self.indentation > 0:
            return re.compile(self._END_REGEX.format(indentation=self.indentation - 1, marker=re.escape(self.marker)))
        else:
            return re.compile(self._ALT_END_REGEX.format(marker=re.escape(self.marker)))


class Document(ContainerBlock):
    _TEMPLATE = "{content}"

    def close_check(self, line, line_number, force=False):
        for child in self.children:
            if not child.closed:
                child.close_check(line, line_number, force)

    @staticmethod
    def new_block(last_open, line, line_number, last, stripped):
        block = None
        if type(last_open) is IndentedCodeBlock or type(last_open) is FencedCodeBlock:
            block = None
        elif ATXHeading.starts(last_open, line, line_number, last):
            block = ATXHeading.create(line, line_number, stripped)
        elif ThematicBreak.starts(last_open, line, line_number, last):
            if type(last_open) is Paragraph and SetextHeading.starts(last_open, line, line_number, last):
                block = None
            else:
                block = ThematicBreak.create(line, line_number, stripped)
        elif IndentedCodeBlock.starts(last_open, line, line_number, last):
            block = IndentedCodeBlock.create(line, line_number, stripped)
        elif FencedCodeBlock.starts(last_open, line, line_number, last):
            block = FencedCodeBlock.create(line, line_number, stripped)
        elif ListItem.starts(last_open, line, line_number, last):
            block = ListItem.create(line, line_number, stripped)
        elif OrderedList.starts(last_open, line, line_number, last):
            block = OrderedList.create(line, line_number, stripped)
        elif BulletList.starts(last_open, line, line_number, last):
            block = BulletList.create(line, line_number, stripped)
        elif BlockQuote.starts(last_open, line, line_number, last):
            block = BlockQuote.create(line, line_number, stripped)
        elif Paragraph.starts(last_open, line, line_number, last):
            block = Paragraph.create(line, line_number, stripped)
        return block

    @staticmethod
    def tab_to_spaces(line, indentation, stripped):
        indent = len(line) if indentation < 0 else indentation
        while "\t" in line[:indent]:
            index = line.find("\t")
            if index < indent:
                line = line.replace("\t", [4, 3, 2, 1][(index + stripped) % 4] * " ", 1)
            indent = len(line) if indentation < 0 else indentation
        return line

    @staticmethod
    def render_inline(text):
        bold = r"(?<!\\)[*]{2}(?P<content>.*?)(\\\\)*(?<!\\)[*]{2}"
        text = re.sub(bold, r"<em>\g<content></em>", text)
        italic = r"(?<!\\)[*](?P<content>.*?)(\\\\)*(?<!\\)[*]"
        text = re.sub(italic, r"<i>\g<content></i>", text)
        return text
