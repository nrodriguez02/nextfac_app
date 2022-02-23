import functools
from typing import Callable
from flask import session, redirect, flash, url_for, request, current_app


def requires_login(f: Callable) -> Callable:
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('email'):
            flash('You are not authorized to this section.', 'warning')
            return redirect(url_for('auth.login_user'))
        return f(*args, **kwargs)

    return decorated_function


def requires_admin(f: Callable) -> Callable:
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('email') != current_app.config.get('ADMIN', ''):
            flash('You need to be an system administrator to access this section', 'danger')
            return redirect(url_for('jobs.index'))
        return f(*args, **kwargs)

    return decorated_function
