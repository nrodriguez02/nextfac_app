from flask import Blueprint, request, render_template, make_response, redirect, url_for, jsonify, session, flash, Markup
from models.user import User, UserErrors
from models.user import requires_login, requires_admin
from common.utils import Utils

user_blueprints = Blueprint("auth", __name__)

view = {
    "title": "Settings",
    "icon": "fa-cog",
    "name": "settings",
    "nav_on": True,
    "search_on": False
}


@user_blueprints.route('/', methods=['GET'])
@requires_login
def index():
    return redirect(url_for('auth.register_user'))


@user_blueprints.route('/register', methods=['GET', 'POST'])
@requires_login
@requires_admin
def register_user():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        area = request.form['area']
        group_id = request.form['group_id']

        try:
            message = Markup('<i class="fa fa-check"></i> User was successfully created!')
            User.register_user(email, password, name, area, group_id)
            flash(message, 'success')
            return redirect(url_for('auth.index'))
        except UserErrors.UserError as e:
            return e.message

    view['title'] = "Setting -> User Registration"

    return render_template("users/register.html", view=view)


@user_blueprints.route('/login', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        remember_me = True if 'remembercheck' in request.form else False

        try:
            User.is_login_valid(email, password)
            session['email'] = email
            session['name'] = User.find_by_email(email).name
            Utils.make_session_permanent(remember_me)
            return redirect(url_for('jobs.index'))
        except UserErrors.UserError as e:
            message = Markup('<i class="fa fa-warning"></i> ' + e.message)
            flash(message, 'warning')

    return render_template("home.html")


@user_blueprints.route('/logout')
@requires_login
def logout():
    session['email'] = None
    session['name'] = None
    return redirect(url_for('auth.login_user'))
