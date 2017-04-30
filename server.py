#!/usr/bin/python3
# -*- coding: utf-8 -*-
from flask import Flask, render_template, request
from parser.gfm import GFMParser

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/to-html", methods=["POST"])
def get_html():
    data = request.get_data(as_text=True)
    print(data)
    try:
        result = GFMParser().parse_text(data).get_html()
        print(result)
        return result
    except:
        return "Error"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8082)