#!/usr/bin/python3
import re


class InlineParser(object):
    @staticmethod
    def parse(input_string):
        parts = []
        delimiter_stack = []
        delimiter_regex = re.compile(r"(.|\n)*?(?P<pre>\S?)(?P<deli>[*]+|[_]+|\[|!\[|])(?P<post>\S?)")
        pos = 0
        while True:
            m = delimiter_regex.match(input_string, pos)
            if m is not None:
                parts.append(input_string[pos:m.end("deli")])
                r = m.groupdict()
                if m.group("deli").startswith("*"):
                    delimiter_stack.append(Delimiter("*", len(m.group("deli")), not r['pre'] and r['post'], r['pre'], len(parts) - 1))
                elif m.group("deli").startswith("_"):
                    delimiter_stack.append(Delimiter("_", len(m.group("deli")), not r['pre'] and r['post'], r['pre'], len(parts) - 1))
                elif m.group("deli") == "[":
                    delimiter_stack.append(Delimiter("[", 1, True, True, len(parts) - 1))
                elif m.group("deli") == "![":
                    delimiter_stack.append(Delimiter("![", 1, True, True, len(parts) - 1))
                else:
                    InlineParser.look_for_link_or_img()
                pos = m.end("deli")
            else:
                parts.append(input_string[pos:])
                break
        emphs = InlineParser.process_emphasis(delimiter_stack, None)
        out = []
        for i, part in enumerate(parts):
            sub = []
            strip = 0
            for e in emphs:
                if e[0].position == i:
                    strip += e[2]
                    if e[2] == 1:
                        sub.append("<em>")
                    elif e[2] == 2:
                        sub.append("<strong>")
                elif e[1].position == i:
                    strip += e[2]
                    if e[2] == 1:
                        sub.append("</em>")
                    elif e[2] == 2:
                        sub.append("</strong>")
            if strip:
                sub.append(part[:-strip])
            else:
                sub.append(part)
            out.extend(sub[::-1])
        if not parts:
            return input_string
        return "".join(out)


    @staticmethod
    def look_for_link_or_img():
        pass

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
                    if cur_del.number == 0:
                        cur_del.active = False
                    if other.number == 0:
                        other.active = False
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
    pass


class Text(Inline):
    pass


class Code(Inline):
    REGEX = re.compile("(?P<span>[`]+)(?P<content>[^`].*?)(?<!`)\1(?!`)")
