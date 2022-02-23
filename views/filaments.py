from flask import Blueprint, request, render_template, make_response, redirect, url_for, flash, Markup
from flask_paginate import Pagination, get_page_parameter

from models.filament import Filament
from models.user.decorators import requires_login, requires_admin

filament_blueprints = Blueprint("filaments", __name__)

view = {
            "title": "Filaments",
            "icon": "fa-cubes",
            "name": "filaments",
            "nav_on": True,
            "search_on": False
        }


@filament_blueprints.route('/', methods=['GET'])
@requires_login
def index():
    page = request.args.get(get_page_parameter(), type=int, default=1)

    per_page = 6
    offset = (page - 1) * per_page

    filaments = Filament.all(offset, per_page)
    counter = len(Filament.all())

    view['title'] = "Filaments"
    view['search_on'] = True

    search = False
    q = request.args.get('q')
    if q:
        search = True

    pagination = Pagination(page=page, per_page=per_page, css_framework='bootstrap4', offset=offset, total=counter,
                            search=search, record_name='filaments')

    return render_template('filaments/index.html', filaments=filaments, pagination=pagination, view=view)


@filament_blueprints.route('/new', methods=['GET', 'POST'])
@requires_login
def new_filament():
    if request.method == 'POST':
        cor = request.form['cor']
        temp = request.form['temp']
        filament_type = request.form['filament_type']
        provider = request.form['provider']
        cost = request.form['cost']
        quality = request.form['quality']
        stock = request.form['stock']
        weight = request.form['weight']
        name = filament_type + "-" + cor + " " + provider + "-" + weight
        hex_cor = request.form['hex_cor']

        if Filament.find_one_by("name", name):
            message = Markup('<i class="fa fa-warning"></i> Error: The filament you are trying to create already exist.')
            flash(message, 'warning')
            view['title'] = "New filament"
            view['search_on'] = False
            return render_template('filaments/new_filament.html', view=view)
        else:
            Filament(cor, temp, filament_type, provider, cost, quality, stock, weight, name, hex_cor).save_to_mongo()
            flash('The filament was successfully created!', 'success')
            return redirect(url_for('filaments.index'))
    else:
        view['title'] = "New filament"
        view['search_on'] = False
        return render_template('filaments/new_filament.html', view=view)


@filament_blueprints.route('/edit/<string:filament_id>', methods=['GET', 'POST'])
@requires_login
def edit_filament(filament_id):
    filament = Filament.get_by_id(filament_id)

    if request.method == 'POST':
        filament.cor = request.form['cor']
        filament.temp = request.form['temp']
        filament.filament_type = request.form['filament_type']
        filament.cost = request.form['cost']
        filament.quality = request.form['quality']
        filament.stock = request.form['stock']
        filament.weight = request.form['weight']
        filament.name = filament.filament_type + "-" + filament.cor + " " + filament.provider + "-" + filament.weight
        filament.hex_cor = request.form['hex_cor']

        x_filament = Filament.find_one_by("name", filament.name)
        if x_filament is not None:
            if x_filament._id != filament_id:
                message = Markup('<i class="fa fa-warning"></i> Error: The filament cannot be created, already exist.')
                flash(message, 'warning')
                view['title'] = "Edit filament"
                view['search_on'] = False
                return render_template('filaments/edit_filament.html', filament=filament, view=view)

        filament.save_to_mongo()
        flash('The filament was updated!', 'success')
        return redirect(url_for('filaments.index'))
    else:
        view['title'] = "Edit filament"
        view['search_on'] = False
        return render_template('filaments/edit_filament.html', filament=filament, view=view)


@filament_blueprints.route('/delete/<string:filament_id>', methods=['GET'])
@requires_login
@requires_admin
def remove_filament(filament_id):
    filament = Filament.get_by_id(filament_id)
    filament.remove_from_mongo()
    flash('The filament was deleted!', 'danger')
    return redirect(url_for('filaments.index'))


@filament_blueprints.route('/search', methods=['POST'])
@requires_login
def search():
    if request.method == 'POST' and request.form['parameter'] != "":
        parameter = request.form['parameter']
        filaments = Filament.get_by_search(parameter)

        page = request.args.get(get_page_parameter(), type=int, default=1)
        counter = len(filaments)
        per_page = counter if counter > 0 else 1
        offset = counter

        view['title'] = "Filaments"
        view['search_on'] = True

        search = False
        q = request.args.get('q')
        if q:
            search = True

        pagination = Pagination(page=page, per_page=per_page, css_framework='bootstrap4', offset=offset, total=counter,
                                search=search, record_name='filaments')

        return render_template('filaments/index.html', filaments=filaments, pagination=pagination, view=view)
    else:
        return redirect(url_for('filaments.index'))
