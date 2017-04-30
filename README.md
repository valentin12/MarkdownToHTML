# Markdown to HTML
Regular expression based Markdown to HTML parser written in Python 3.
It's based on the [GitHub Flavored Markdown Spec](https://github.github.com/gfm/)

### Supported
* Thematic breaks
* ATX headings
* Setext headings
* Indented code blocks
* Fenced code blocks
* Paragraphs
* Block Quotes
* Lists
* Emphasis

### Not Supported
* All inlines except for emphasis
* HTML blocks
* Link reference definitions
* Escaped characters
* Extensions

## Usage
### Module
``` python
    from parser.gfm import GFMParser

    text = "**Hello world**"
    parser = GFMParser()

    parser.parse_text(text)
    print(parser.get_html())
    # <p><strong>Hello world</strong></p>
```

### Program

    $ python3 convert.py input.md

## Server
A basic flask server can be used to serve a website for dynamically typing and converting the text.
It will start on http://0.0.0.0:8082

## Tests
The results can be tested with the [CommonMark examples](https://github.com/jgm/CommonMark).

```
$ cd CommonMark/
$ ./test/spec_tests.py -p ~/MarkdownToHTML/run_tests.py
```

Currently 320 of 621 tests pass
