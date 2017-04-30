#!/usr/bin/python3
import re
import string


class InlineParser(object):
    @staticmethod
    def parse(input_string):
        code = re.compile(r"[\s\S]*?(?P<tick>`+)(?P<content>[\s\S]*?)(?<=[^`])\1((?!`)|$)")
        pos = 0
        parts = []
        while pos < len(input_string):
            m = code.match(input_string, pos)
            if m is not None:
                r = m.groupdict()
                if pos != m.start('tick'):
                    parts.append(Text(input_string[pos:m.start('tick')]))
                parts.append(CodeSpan(r['content']))
                pos = m.end()
            else:
                parts.append(Text(input_string[pos:]))
                break
        out = []
        for part in parts:
            if type(part) in [Text]:
                out.extend(InlineParser.get_emphasis(part.text))
            else:
                out.append(part)
        return "".join([e.get_html() for e in out])


    @staticmethod
    def look_for_link_or_img():
        pass

    @staticmethod
    def get_emphasis(text):
        delimiter_stack = []
        delimiter_regex = re.compile(r"[\s\S]*?(?P<pre>[^_*\s\]!\[]?)(?P<deli>[*]+|[_]+|\[|!\[|])(?P<post>\S?)")
        pos = 0
        parts = []
        while True:
            m = delimiter_regex.match(text, pos)
            if m is not None:
                parts.append(text[pos:m.end("deli")])
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
                parts.append(text[pos:])
                break
        emphs = InlineParser.process_emphasis(delimiter_stack, None)
        used = []
        out = []
        for e in emphs:
            parts[e[0].position] = parts[e[0].position][:-e[2]]
            text = ""
            for i in range(e[0].position + 1, e[1].position):
                used.append(i)
                text += parts[i]
            text += parts[e[1].position][:-e[2]]
            used.append(e[1].position)
            out.append((Emphasis(text=text, strong=e[2] > 1), e[0].position + 1))
        for i, part in enumerate(parts):
            if i not in used:
                out.append((Text(part), i))
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
    pass


class SoftBreak(Inline):
    pass


class Emphasis(Inline):
    _TEMPLATE_EM = "<em>{content}</em>"
    _TEMPLATE_STRONG = "<strong>{content}</strong>"

    def __init__(self, text="", strong=False):
        self.text = text
        self.strong = strong

    def get_html(self):
        if not self.text:
            return ""
        if self.strong:
            return self._TEMPLATE_STRONG.format(content=self.text)
        else:
            return self._TEMPLATE_EM.format(content=self.text)


class Text(Inline):
    def __init__(self, text=""):
        self.text = text

    def get_html(self):
        return self.text


class CodeSpan(Inline):
    _TEMPLATE = "<code>{content}</code>"

    def __init__(self, text=""):
        self.text = text

    def get_html(self):
        return self._TEMPLATE.format(content=self.text.strip())


class Code(Inline):
    REGEX = re.compile("(?P<span>[`]+)(?P<content>[^`].*?)(?<!`)\1(?!`)")
