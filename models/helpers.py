import os
from flask import url_for


def static_file(filename, pdf=False):
    if (pdf):
        basedir = os.path.abspath(os.path.dirname(__file__))
        directory = os.path.normpath(os.path.join(basedir, '..'))
        return "".join([directory, "/static/", filename])
    else:
        return url_for('static', filename=filename)
