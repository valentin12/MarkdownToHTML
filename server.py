#!/usr/bin/python3
# -*- coding: utf-8 -*-
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

from flask import Flask, render_template, request
from parser.gfm import GFMParser

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/to-html", methods=["POST"])
def get_html():
    """Return converted MD"""
    data = request.get_data(as_text=True)
    result = GFMParser().parse_text(data).get_html()
    return result


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8082)