#!/usr/bin/python3
import re

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
    def create(cls, line, line_number):
        return cls()

    def get_html(self):
        return self._TEMPLATE.format(**self.__dict__)

    def get_end_regex(self):
        return re.compile(self._END_REGEX)

    def close_check(self, line, line_number):
        pass

    def strip_line(self, line):
        return line

    def add_line(self, line):
        self.lines.append(line)

    def get_last_open(self, line):
        cur_line = self.strip_line(line)
        line = cur_line
        last = self
        for child in self.children:
            if not (child.closed or child.close_next):
                last, line = child.get_last_open(cur_line)
        return last, line

    def close_marked(self):
        if self.close_next:
            self.closed = True
        for child in self.children:
            if not child.closed:
                child.close_marked()


class LeafBlock(Block):
    def close_check(self, line, line_number):
        self.close_next = True
        return line

    def get_html(self):
        lines = self.lines
        while not self.lines[-1].strip():
            lines = lines[:-1]
        return self._TEMPLATE.format(content="".join(lines), **self.__dict__)


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


# Leaf blocks
class ThematicBreak(LeafBlock):
    _TEMPLATE = "<hr />"
    START_REGEX = re.compile(r"^ {0,3}([*\-_])[ ]*(\1[ ]*){2,}(\1|[ ])*\n?$")

    @classmethod
    def create(cls, line, line_number):
        return cls()


class ATXHeading(LeafBlock):
    _TEMPLATE = "<h{number}>{content}</h{number}>"
    REGEX = re.compile(r"^(?P<number>[#]{1,6})[ \t]*(?P<content>.*?(?:\#*))[ \t]*(?:[#]{2,})? *\n?$")
    START_REGEX = re.compile(r"^(?P<number>[#]{1,6})[ \t]*")

    def __init__(self, number=1):
        super().__init__()
        self.number = number

    @classmethod
    def create(cls, line, line_number):
        r = cls.REGEX.match(line).groupdict()
        instance = cls(len(r['number']))
        instance.add_line(r['content'])
        return instance


class SetextHeading(LeafBlock):
    _TEMPLATE = "<h{number}>{content}</{number}>"
    REGEX = re.compile(r"^ {0,3}([=\-])\1* *\n?$")
    START_REGEX = REGEX


class IndentedCodeBlock(LeafBlock):
    _TEMPLATE = "<pre><code>{content}</code></pre>"
    REGEX = re.compile(r"^([ ]{4}|\t)(?P<content>.*\n?)$")
    START_REGEX = re.compile(r"^([ ]{4}|\t)")
    _END_REGEX = r"^ {0,3}\S+"

    @classmethod
    def create(cls, line, line_number):
        instance = cls()
        instance.add_line(line)
        return instance

    def add_line(self, line):
        line = Document.tab_to_spaces(line, 4)
        self.lines.append(line[4:])

    def close_check(self, line, line_number):
        self.close_next = re.compile(self._END_REGEX).match(line) is not None


class FencedCodeBlock(LeafBlock):
    _TEMPLATE = "<pre><code{class_str}>{content}</code></pre>"
    REGEX = re.compile(r"^(?P<indentation>[ ]{0,3})(?P<fence>(?P<character>[`~])\3{2,})[ \t]*(?P<info>[^`]*?)?[ \t]*\n?$")
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
    def create(cls, line, line_number):
        r = cls.REGEX.match(line).groupdict()
        return cls(r['character'], len(r['indentation']), len(r['fence']), r['info'])

    def close_check(self, line, line_number):
        self.close_next = self.get_end_regex().match(line) is not None

    def get_end_regex(self):
        return re.compile(self._END_REGEX.format(**self.__dict__))


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
    _TEMPLATE = "<p>{content}</p>"
    START_REGEX = re.compile(r"[\s]*\S+")

    def __init__(self):
        super().__init__()
        self.setextheading = False

    @classmethod
    def create(cls, line, line_number):
        instance = cls()
        instance.add_line(line)
        return instance

    def close_check(self, line, line_number):
        self.close_next = not line.strip()
        if (ThematicBreak.START_REGEX.match(line) is not None and SetextHeading.START_REGEX.match(line) is None) \
                or ATXHeading.START_REGEX.match(line) is not None \
                or FencedCodeBlock.START_REGEX.match(line) is not None \
                or BlockQuote.START_REGEX.match(line) is not None \
                or BulletList.START_REGEX.match(line) is not None \
                or (OrderedList.START_REGEX.match(line) is not None and line.startswith("1.") or line.startswith("1)")):
            self.close_next = True


# Container blocks
class BlockQuote(ContainerBlock):
    _TEMPLATE = "<blockquote>\n{content}</blockquote>"
    REGEX = re.compile(r"^ {0,3}>[ \t]*(?P<content>.*\n?)$")
    START_REGEX = re.compile(r"^ {0,3}\>")
    _END_REGEX = re.compile(r"^(?! {0,3}\>)")

    def close_check(self, line, line_number):
        if self.get_end_regex().match(line):
            self.close_next = True
        else:
            self.close_next = False
            line = self.strip_line(line)
            for child in self.children:
                if not child.closed:
                    child.close_check(line, line_number)

    def strip_line(self, line):
        return self.REGEX.match(line).groupdict()['content']


class ListItem(ContainerBlock):
    _TEMPLATE = "<li>{content}</li>"
    REGEX = re.compile(r"^(?P<indentation>(([\d]{1,9}[.)])|[\-+*])[ \t]*)(?P<content>.*\n?)$")
    _END_REGEX = r"^[ ]{{0,{indentation}}}\S.*"

    def __init__(self,indentation, start_line):
        super().__init__()
        self.indentation = indentation
        self.start_line = start_line

    @classmethod
    def create(cls, line, start_line=0):
        r = cls.REGEX.match(line).groupdict()
        return cls(len(Document.tab_to_spaces(r['indentation'], -1)) - 1, start_line)

    def close_check(self, line, line_number):
        self.close_next = self.get_end_regex().match(line) and not line_number == self.start_line

    def strip_line(self, line):
        return Document.tab_to_spaces(line, self.indentation)[self.indentation:]

    def get_end_regex(self):
        return re.compile(self._END_REGEX.format(**self.__dict__))


class OrderedList(ContainerBlock):
    _TEMPLATE = "<ol start={start}>\n{content}\n</ol>"
    REGEX = re.compile(r"^(?P<indentation>(?P<start>[\d]{1,9})[.)][ \t]*)(?P<content>.*\n?)$")
    START_REGEX = re.compile(r"^(?P<indentation>(?P<start>[\d]{1,9})[.)][ \t]*)")
    _END_REGEX = r"^(?!([\d]{{1,9}}[.)])|(?![ ]{{0,{indentation}}}\S.*))"

    def __init__(self, start, indentation):
        super().__init__()
        self.start = start
        self.indentation = indentation

    @classmethod
    def create(cls, line, line_number):
        r = cls.REGEX.match(line).groupdict()
        instance = cls(int(r['start']), len(Document.tab_to_spaces(r['indentation'], -1)) - 1)
        instance.add(ListItem.create(line, line_number))
        return instance

    def close_check(self, line, line_number):
        if self.get_end_regex().match(line) is not None:
            self.close_next = True
        else:
            self.close_next = False
            line = self.strip_line(line)
            for child in self.children:
                if not child.closed:
                    child.close_check(line, line_number)

    def get_end_regex(self):
        return re.compile(self._END_REGEX.format(**self.__dict__))


class BulletList(ContainerBlock):
    _TEMPLATE = "<ul>\n{content}\n</ul>"
    REGEX = re.compile(r"^(?P<indentation>(?P<marker>[\-+*][ \t]*))(?P<content>.*\n?)$")
    START_REGEX = re.compile(r"^(?P<indentation>(?P<marker>[\-+*][ \t]+))")
    _END_REGEX = r"^(?!([{marker}][ \t])|(?![ ]{{0,{indentation}}}\S.*))"

    def __init__(self, marker, indentation):
        super().__init__()
        self.marker = marker
        self.indentation = indentation

    @classmethod
    def create(cls, line, line_number):
        r = cls.REGEX.match(line).groupdict()
        instance = cls(r['marker'], len(Document.tab_to_spaces(r['indentation'], -1)) - 1)
        instance.add(ListItem.create(line, line_number))
        return instance

    def close_check(self, line, line_number):
        if self.get_end_regex().match(line) is not None:
            self.close_next = True
        else:
            self.close_next = False
            line = self.strip_line(line)
            for child in self.children:
                if not child.closed:
                    child.close_check(line, line_number)

    def get_end_regex(self):
        return re.compile(self._END_REGEX.format(**self.__dict__))


class Document(ContainerBlock):
    _TEMPLATE = "{content}"

    def close_check(self, line, line_number):
        for child in self.children:
            if not child.closed:
                child.close_check(line, line_number)

    @staticmethod
    def new_block(line, last, line_number):
        block = None
        if type(last) is IndentedCodeBlock or type(last) is FencedCodeBlock:
            block = None
        elif ATXHeading.START_REGEX.match(line) is not None:
            block = ATXHeading.create(line, line_number)
        elif ThematicBreak.START_REGEX.match(line) is not None:
            if type(last) is Paragraph and SetextHeading.START_REGEX.match(line) is not None:
                last.add_line(line)
                last.closed = True
                last.setextheading = True
                return None
            else:
                block = ThematicBreak.create(line, line_number)
        elif IndentedCodeBlock.START_REGEX.match(Document.tab_to_spaces(line, 4)) is not None \
                and not type(last) is Paragraph:
            block = IndentedCodeBlock.create(line, line_number)
        elif FencedCodeBlock.START_REGEX.match(line) is not None:
            block = FencedCodeBlock.create(line, line_number)
        elif type(last) is BulletList or type(last) is OrderedList \
                and ListItem.START_REGEX.match(line):
            block = ListItem.create(line, line_number)
        elif OrderedList.START_REGEX.match(line) is not None:
            block = OrderedList.create(line, line_number)
        elif BulletList.START_REGEX.match(line) is not None:
            block = BulletList.create(line, line_number)
        elif BlockQuote.START_REGEX.match(line) is not None:
            block = BlockQuote.create(line, line_number)
        elif type(last) is not Paragraph and Paragraph.START_REGEX.match(line):
            block = Paragraph.create(line, line_number)
        return block


    @staticmethod
    def tab_to_spaces(line, indentation):
        n = 1
        indent = len(line) if indentation < 0 else indentation
        while "\t" in line[:indent] and n:
            line, n = re.subn(r"(?<!\S)\t", "    ", line, count=1)
            indent = len(line) if indentation < 0 else indentation
        return line

    @staticmethod
    def render_inline(text):
        bold = r"(?<!\\)[*]{2}(?P<content>.*?)(\\\\)*(?<!\\)[*]{2}"
        text = re.sub(bold, r"<em>\g<content></em>", text)
        italic = r"(?<!\\)[*](?P<content>.*?)(\\\\)*(?<!\\)[*]"
        text = re.sub(italic, r"<i>\g<content></i>", text)
        return text
