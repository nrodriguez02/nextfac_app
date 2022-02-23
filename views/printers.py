from flask import Blueprint, request, render_template, make_response, redirect, jsonify, url_for, flash, Markup
from flask_paginate import Pagination, get_page_parameter
from models.printer import Printer
from models.user.decorators import requires_login, requires_admin

printer_blueprints = Blueprint("printers", __name__)

view = {
    "title": "Printers",
    "icon": "fa-print",
    "name": "printers",
    "nav_on": True,
    "search_on": False
}


@printer_blueprints.route('/')
@requires_login
def index():
    page = request.args.get(get_page_parameter(), type=int, default=1)

    per_page = 6
    offset = (page - 1) * per_page

    printers = Printer.all(offset, per_page)
    counter = len(Printer.all())

    view['title'] = "Printers"
    view['search_on'] = True

    search = False
    q = request.args.get('q')
    if q:
        search = True

    pagination = Pagination(page=page, per_page=per_page, css_framework='bootstrap4', offset=offset, total=counter,
                            search=search, record_name='printers')

    return render_template('printers/index.html', printers=printers, pagination=pagination, view=view)


@printer_blueprints.route('/new', methods=['GET', 'POST'])
@requires_login
def new_printer():
    if request.method == 'POST':
        name = request.form['name']
        url = request.form['url']
        apikey = request.form['apikey']
        server = True if 'server' in request.form else False

        if Printer.find_one_by("name", name) or Printer.find_one_by("url", url):
            message = Markup(
                '<i class="fa fa-warning"></i> Error: The printer/url you are trying to create already exist.')
            flash(message, 'warning')
            view['title'] = "New Printer"
            view['search_on'] = False
            return render_template('printers/new_printer.html', view=view)
        else:
            Printer(name, url, apikey, server).save_to_mongo()
            flash('The printer was successfully created!', 'success')
            return redirect(url_for('printers.index'))
    else:
        view['title'] = "New printer"
        view['search_on'] = False
        return render_template('printers/new_printer.html', view=view)


@printer_blueprints.route('/edit/<string:printer_id>', methods=['GET', 'POST'])
@requires_login
def edit_printer(printer_id):
    printer = Printer.get_by_id(printer_id)

    if request.method == 'POST':
        printer.name = request.form['name']
        printer.url = request.form['url']
        printer.apikey = request.form['apikey']
        printer.server = True if 'server' in request.form else False

        x_printer = Printer.find_one_by("url", printer.url)
        if x_printer is not None:
            if x_printer._id != printer_id:
                message = Markup('<i class="fa fa-warning"></i> Error: The printer cannot be created, already exist.')
                flash(message, 'warning')
                view['title'] = "Edit printer"
                view['search_on'] = False
                return render_template('printers/edit_printer.html', printer=printer, view=view)

        printer.save_to_mongo()
        flash('The printer was updated!', 'success')
        return redirect(url_for('printers.index'))
    else:
        view['title'] = "Edit printer"
        view['search_on'] = False
        return render_template('printers/edit_printer.html', printer=printer, view=view)


@printer_blueprints.route('/delete/<string:printer_id>', methods=['GET'])
@requires_login
@requires_admin
def remove_printer(printer_id):
    printer = Printer.get_by_id(printer_id)
    printer.remove_from_mongo()
    flash('The printer was deleted!', 'danger')
    return redirect(url_for('printers.index'))


@printer_blueprints.route('/search', methods=['POST'])
@requires_login
def search():
    if request.method == 'POST' and request.form['parameter'] != "":
        parameter = request.form['parameter']
        printers = Printer.get_by_search(parameter)

        page = request.args.get(get_page_parameter(), type=int, default=1)
        counter = len(printers)
        per_page = counter if counter > 0 else 1
        offset = counter

        view['title'] = "Printers"
        view['search_on'] = True

        search = False
        q = request.args.get('q')
        if q:
            search = True

        pagination = Pagination(page=page, per_page=per_page, css_framework='bootstrap4', offset=offset, total=counter,
                                search=search, record_name='printers')

        return render_template('printers/index.html', printers=printers, pagination=pagination, view=view)
    else:
        return redirect(url_for('printers.index'))


@printer_blueprints.route('/dashboard', methods=['GET'])
@requires_login
def dashboard():
    view['title'] = "Dashboard"
    view["icon"] = "fa-dashboard"
    view['search_on'] = False

    return render_template('printers/dashboard.html', view=view)


@printer_blueprints.route('/dashboard_update', methods=['GET'])
@requires_login
def dashboard_update():
    history, left_time = Printer.history_threads()
    result = render_template('printers/thread_dashboard.html', history=history, left_time=left_time)
    return jsonify(result=result)


@printer_blueprints.route('/start/printer_id=<string:printer_id>', methods=['GET'])
@requires_login
def start(printer_id):
    printer = Printer.get_by_id(printer_id)
    if printer.start_job():
        return jsonify(result=True)

    return jsonify(result=False)


@printer_blueprints.route('/pause/printer_id=<string:printer_id>', methods=['GET'])
@requires_login
def pause(printer_id):
    printer = Printer.get_by_id(printer_id)
    if printer.pause_job():
        return jsonify(result=True)

    return jsonify(result=False)


@printer_blueprints.route('/stop/printer_id=<string:printer_id>', methods=['GET'])
@requires_login
def stop(printer_id):
    printer = Printer.get_by_id(printer_id)
    if printer.stop_job():
        return jsonify(result=True)

    return jsonify(result=False)


@printer_blueprints.route('/connect/printer_id=<string:printer_id>', methods=['GET'])
@requires_login
def connect(printer_id):
    printer = Printer.find_one_by("_id", printer_id)
    if printer.connect():
        return jsonify(result=True)

    return jsonify(result=False)
