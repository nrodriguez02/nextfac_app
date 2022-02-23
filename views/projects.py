import re
import datetime

from flask import Blueprint, request, render_template, make_response, redirect, url_for, flash, Markup, current_app
from flask_paginate import Pagination, get_page_parameter
from werkzeug.utils import secure_filename

from models.project import Project
from models.user.decorators import requires_login, requires_admin
from common.utils import Utils
import os

project_blueprints = Blueprint("projects", __name__)

view = {
    "title": "Projects",
    "icon": "fa-puzzle-piece",
    "name": "projects",
    "nav_on": True,
    "search_on": False
}


@project_blueprints.route('/', methods=['GET'])
@requires_login
def index():
    page = request.args.get(get_page_parameter(), type=int, default=1)

    per_page = 8
    offset = (page - 1) * per_page if page > 0 else 1

    projects = Project.all(offset, per_page)
    counter = len(Project.all())

    view['title'] = "Projects"
    view['search_on'] = True

    search = False
    q = request.args.get('q')
    if q:
        search = True

    pagination = Pagination(page=page, per_page=per_page, css_framework='bootstrap4', offset=offset, total=counter,
                            search=search, record_name='projects')

    return render_template('projects/index.html', projects=projects, pagination=pagination, view=view)


@project_blueprints.route('/search', methods=['POST'])
@requires_login
def search():
    if request.method == 'POST' and request.form['parameter'] != "":
        parameter = request.form['parameter']
        projects = Project.get_by_search(parameter)

        page = request.args.get(get_page_parameter(), type=int, default=1)
        counter = len(projects)
        per_page = counter if counter > 0 else 1
        offset = counter

        view['title'] = "Projects"
        view['search_on'] = True

        search = False
        q = request.args.get('q')
        if q:
            search = True

        pagination = Pagination(page=page, per_page=per_page, css_framework='bootstrap4', offset=offset, total=counter,
                                search=search, record_name='projects')

        return render_template('projects/index.html', projects=projects, pagination=pagination, view=view)
    else:
        return redirect(url_for('projects.index'))


@project_blueprints.route('/new', methods=['GET', 'POST'])
@requires_login
def new_project():
    if request.method == 'POST':
        file = request.files['file']

        temp_path = current_app.config.get('TEMPORAL_FOLDER', '')

        if not os.path.exists(temp_path):
            os.makedirs(temp_path)

        file_url_temp = os.path.join(temp_path, secure_filename(file.filename))
        file.save(file_url_temp)

        name = re.sub('.gcode', '', str(file.filename))
        time = Utils.get_print_time(file_url_temp)
        weight = Utils.get_weight(file_url_temp)

        upd_project = Project.find_one_by("name", name)
        if upd_project:

            upload_path = current_app.config.get('UPLOAD_FOLDER', '')

            if not os.path.exists(upload_path):
                os.makedirs(upload_path)

            file_url = os.path.join(upload_path, secure_filename(file.filename))
            os.replace(file_url_temp, file_url)
            path = file_url

            upd_project.name = name
            upd_project.time = time
            upd_project.weight = weight
            upd_project.path = path

            upd_project.save_to_mongo()
            return "The project was updated!", 200
        else:
            upload_path = current_app.config.get('UPLOAD_FOLDER', '')

            if not os.path.exists(upload_path):
                os.makedirs(upload_path)

            file_url = os.path.join(upload_path, secure_filename(file.filename))
            os.replace(file_url_temp, file_url)
            path = file_url
            Project(name, time, weight, path).save_to_mongo()
            return "Upload project successfully", 200
    else:
        view['title'] = "New Project"
        view['search_on'] = False
        return render_template('projects/dragndrop.html', view=view)


@project_blueprints.route('/edit/<string:project_id>', methods=['GET', 'POST'])
@requires_login
def edit_project(project_id):
    project = Project.get_by_id(project_id)

    if request.method == 'POST':
        project.name = request.form['name']
        project.time = request.form['time']
        project.weight = request.form['weight']
        project.path = request.form['path']

        x_project = Project.find_one_by("name", project.name)
        if x_project is not None:
            if x_project._id != project_id:
                message = Markup('<i class="fa fa-warning"></i> Error: The project cannot be created, already exist.')
                flash(message, 'warning')
                view['title'] = "Edit project"
                view['search_on'] = False
                return render_template('projects/edit_project.html', project=project, view=view)

        project.save_to_mongo()
        flash('The project was updated!', 'success')
        return redirect(url_for('projects.index'))
    else:
        view['title'] = "Edit project"
        view['search_on'] = False
        return render_template('projects/edit_project.html', project=project, view=view)


@project_blueprints.route('/delete/<string:project_id>', methods=['GET'])
@requires_login
@requires_admin
def remove_project(project_id):
    project = Project.get_by_id(project_id)
    file_url = project.path
    os.remove(file_url)
    project.remove_from_mongo()
    flash('The project was deleted!', 'danger')
    return redirect(url_for('projects.index'))
