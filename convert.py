#!/usr/bin/python3
from parser.gfm import GFMParser
import argparse

if __name__ == '__main__':
    argp = argparse.ArgumentParser(description="Convert Markdown to HTML")
    argp.add_argument('file', help="Input markdown file")

    args = argp.parse_args()
    with open(args.file) as f:
        parser = GFMParser()
        parser.parse_text(f.read())
        print(parser.get_html())
