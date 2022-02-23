from datetime import datetime
from flask import Blueprint, request, render_template, make_response, redirect, url_for, jsonify, flash, Markup
from flask_paginate import Pagination, get_page_parameter
import pdfkit

from models.filament import Filament
from models.job import Job
from models.printer import Printer
from models.project import Project
from models.shift import Shift
from models.user.decorators import requires_login, requires_admin
import time

job_blueprints = Blueprint("jobs", __name__)

view = {
        "title": "Job List",
        "icon": "fa-archive",
        "name": "jobs",
        "nav_on": True,
        "search_on": False
    }


@job_blueprints.route('/', methods=['GET'])
@requires_login
def index():

    counter = Job.jobs_amount()
    jobs = Job.all()

    page = request.args.get(get_page_parameter(), type=int, default=1)

    per_page = 8
    offset = 4 * page
    start = (page - 1) * 4

    search = False
    q = request.args.get('q')
    if q:
        search = True

    view['title'] = "Jobs"
    view['search_on'] = True

    pagination = Pagination(page=page, per_page=per_page, css_framework='bootstrap4', offset=offset, total=counter,
                            search=search, record_name='jobs')

    return render_template('jobs/index.html', jobs=jobs, now=datetime.today().strftime('%Y-%m-%d'),
                           pagination=pagination, offset=offset, start=start, view=view)


@job_blueprints.route('/new', methods=['GET', 'POST'])
@requires_login
def new_job():
    if request.method == 'POST':
        orders = request.form.getlist('order_id[]')
        printers = request.form.getlist('printer_id[]')
        projects = request.form.getlist('project_id[]')
        filaments = request.form.getlist('filament_id[]')
        list_obs = request.form.getlist('obs[]')
        date = request.form['date']
        shift_id = request.form['shift_id']
        for count in range(len(printers)):
            order_id = orders[count]
            printer_id = printers[count]
            project_id = projects[count]
            filament_id = filaments[count]
            obs = list_obs[count]
            status = True
            job = Job(date, order_id, shift_id, printer_id, project_id, filament_id, obs, status)
            if not job.job_exist():
                job.save_to_mongo()

        for printer in Printer.all():
            order_id = ""
            printer_id = printer._id
            project_id = None
            filament_id = None
            obs = ""
            status = False
            job = Job(date, order_id, shift_id, printer_id, project_id, filament_id, obs, status)
            if not job.job_exist():
                job.save_to_mongo()

        flash('The job was created!', 'success')
        return redirect(url_for('jobs.index'))
    else:

        view['title'] = "New jobs"
        view['search_on'] = False

        shifts = Shift.all()
        printers = Printer.all()
        projects = Project.all()
        filaments = Filament.all()
        latest_jobs = Job.get_latest_jobs()
        return render_template('jobs/new_job.html', shifts=shifts, printers=printers, projects=projects,
                               filaments=filaments, latest_jobs=latest_jobs, view=view)


@job_blueprints.route('/edit/<string:job_id>', methods=['GET', 'POST'])
@requires_login
def edit_job(job_id):
    job = Job.get_by_id(job_id)
    filaments = Filament.all()
    projects = Project.all()

    if request.method == 'POST':
        job.order_id = request.form['order_id'] if 'order_id' in request.form else ""
        job.project_id = request.form['project_id'] if 'project_id' in request.form else None
        job.filament_id = request.form['filament_id'] if 'filament_id' in request.form else None
        job.obs = request.form['obs'] if 'obs' in request.form else ""
        job.status = True if 'project_id' in request.form else False
        job.save_to_mongo()
        flash('The job was updated!', 'success')
        return redirect(url_for('jobs.index'))

    else:
        view['title'] = "Edit jobs"
        view['search_on'] = False
        return render_template('jobs/edit_job.html', job=job, filaments=filaments, projects=projects, view=view)


@job_blueprints.route('/delete/date=<string:date>shift_id=<string:shift_id>', methods=['GET'])
@requires_login
def remove_job(date, shift_id):
    jobs = Job.find_many_by_date_shift(date, shift_id)
    for job in jobs:
        job.remove_from_mongo()
    flash('The job was deleted!', 'danger')
    return redirect(url_for('jobs.index'))


@job_blueprints.route('/search', methods=['POST'])
@requires_login
def search():
    if request.method == 'POST' and request.form['parameter'] != "":
        parameter = request.form['parameter']
        jobs = Job.get_by_search(parameter)

        counter = Job.search_amount(parameter)

        page = request.args.get(get_page_parameter(), type=int, default=1)

        per_page = counter if counter > 0 else 1
        offset = counter
        start = 0

        view['title'] = "Edit jobs"
        view['search_on'] = True

        search = False
        q = request.args.get('q')
        if q:
            search = True

        pagination = Pagination(page=page, per_page=per_page, css_framework='bootstrap4', offset=offset, total=counter,
                                search=search, record_name='jobs')

        return render_template('jobs/index.html', jobs=jobs, now=datetime.today().strftime('%Y-%m-%d'),
                               pagination=pagination, offset=offset, start=start, view=view)
    else:
        return redirect(url_for('jobs.index'))


@job_blueprints.route('/heat/date=<string:date>shift_id=<string:shift_id>', methods=['GET'])
@requires_login
def heat_printers(date, shift_id):
    jobs = Job.find_many_by_date_shift(date, shift_id)
    for job in jobs:
        if job.status is True:
            Printer.heat(job.printer_id)
    return redirect(url_for('jobs.index'))


@job_blueprints.route('/start/date=<string:date>shift_id=<string:shift_id>', methods=['GET'])
@requires_login
def start_jobs(date, shift_id):
    status = Job.start_all(date, shift_id)
    # status has [empty] if all printers are ok or an [array] whit the printers and error messages for passing to modal
    result = render_template('jobs/partial_check.html', status=status)
    return jsonify(result=result)


@job_blueprints.route('/start_one/job_id=<string:job_id>', methods=['GET'])
@requires_login
def start_one(job_id):
    if Job.start_one(job_id):
        return True  # return tem que ser um redirect


@job_blueprints.route('/connectall/date=<string:date>shift_id=<string:shift_id>', methods=['GET'])
@requires_login
def connect_all(date, shift_id):
    status = Job.connect_all(date, shift_id)
    # status has [empty] if all printers are ok or an [array] whit the printers and error messages for passing to modal
    result = render_template('jobs/partial_check.html', status=status)
    return jsonify(result=result)


@job_blueprints.route('/print_jobs/date=<string:date>shift_id=<string:shift_id>', methods=['GET'])
@requires_login
def print_jobs(date, shift_id):
    jobs = Job.find_many_by_date_shift(date, shift_id)
    rendered = render_template('jobs/print.html', jobs=jobs)
    config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
    pdf = pdfkit.from_string(rendered, False, configuration=config)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    return response


@job_blueprints.route('/check_availability/date=<string:date>shift_id=<string:shift_id>', methods=['GET'])
@requires_login
def check_availability(date, shift_id):
    job_exist = Job.find_many_by_date_shift(date, shift_id)
    if len(job_exist) == 0:
        return jsonify(exist=False)
    else:
        return jsonify(exist=True)
