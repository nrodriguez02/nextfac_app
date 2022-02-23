from flask import Blueprint, request, render_template, make_response, redirect, url_for, flash, Markup
from flask_paginate import Pagination, get_page_parameter
from models.shift import Shift
from models.user.decorators import requires_login, requires_admin

shift_blueprints = Blueprint("shifts", __name__)

view = {
            "title": "Shifts",
            "icon": "fa-clock-o",
            "name": "shifts",
            "nav_on": True,
            "search_on": False
        }


@shift_blueprints.route('/')
@requires_login
def index():
    page = request.args.get(get_page_parameter(), type=int, default=1)

    per_page = 6
    offset = (page - 1) * per_page

    shifts = Shift.all(offset, per_page)
    counter = len(Shift.all())

    view['title'] = "Shifts"
    view['search_on'] = True

    search = False
    q = request.args.get('q')
    if q:
        search = True

    pagination = Pagination(page=page, per_page=per_page, css_framework='bootstrap4', offset=offset, total=counter,
                            search=search, record_name='shifts')

    return render_template('shifts/index.html', shifts=shifts, pagination=pagination, view=view)


@shift_blueprints.route('/new', methods=['GET', 'POST'])
@requires_login
def new_shift():
    if request.method == 'POST':
        desc = request.form['desc']
        timein = request.form['timein']
        timeout = request.form['timeout']

        if Shift.find_one_by("desc", desc):
            message = Markup('<i class="fa fa-warning"></i> Error: The shift you are trying to create already exist.')
            flash(message, 'warning')
            view['title'] = "New Shift"
            view['search_on'] = False
            return render_template('shifts/new_shift.html', view=view)
        else:
            Shift(desc, timein, timeout).save_to_mongo()
            flash('The printer was successfully created!', 'success')
            return redirect(url_for('shifts.index'))
    else:
        view['title'] = "New shift"
        view['search_on'] = False
        return render_template('shifts/new_shift.html', view=view)


@shift_blueprints.route('/edit/<string:shift_id>', methods=['GET', 'POST'])
@requires_login
def edit_shift(shift_id):
    shift = Shift.get_by_id(shift_id)

    if request.method == 'POST':
        shift.desc = request.form['desc']
        shift.timein = request.form['timein']
        shift.timeout = request.form['timeout']

        x_shift = Shift.find_one_by("desc", shift.desc)
        if x_shift is not None:
            if x_shift._id != shift_id:
                message = Markup('<i class="fa fa-warning"></i> Error: The shift cannot be created, already exist.')
                flash(message, 'warning')
                view['title'] = "Edit shift"
                view['search_on'] = False
                return render_template('shifts/edit_shift.html', shift=shift, view=view)

        shift.save_to_mongo()
        flash('The shift was updated!', 'success')
        return redirect(url_for('shifts.index'))
    else:
        view['title'] = "Edit shift"
        view['search_on'] = False
        return render_template('shifts/edit_shift.html', shift=shift, view=view)


@shift_blueprints.route('/delete/<string:shift_id>', methods=['GET'])
@requires_login
@requires_admin
def remove_shift(shift_id):
    shift = Shift.get_by_id(shift_id)
    shift.remove_from_mongo()
    flash('The shift was deleted!', 'danger')
    return redirect(url_for('shifts.index'))


@shift_blueprints.route('/search', methods=['POST'])
@requires_login
def search():
    if request.method == 'POST' and request.form['parameter'] != "":
        parameter = request.form['parameter']
        shifts = Shift.get_by_search(parameter)

        page = request.args.get(get_page_parameter(), type=int, default=1)
        counter = len(shifts)
        per_page = counter if counter > 0 else 1
        offset = counter

        view['title'] = "Shifts"
        view['search_on'] = True

        search = False
        q = request.args.get('q')
        if q:
            search = True

        pagination = Pagination(page=page, per_page=per_page, css_framework='bootstrap4', offset=offset, total=counter,
                                search=search, record_name='shifts')

        return render_template('shifts/index.html', shifts=shifts, pagination=pagination, view=view)
    else:
        return redirect(url_for('shifts.index'))
