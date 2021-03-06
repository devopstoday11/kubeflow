import logging
import os

from flask import Blueprint, current_app, request
from werkzeug.exceptions import Unauthorized

from . import config

bp = Blueprint("authn", __name__)
log = logging.getLogger(__name__)

USER_HEADER = os.getenv("USERID_HEADER", "kubeflow-userid")
USER_PREFIX = os.getenv("USERID_PREFIX", ":")


def get_username():
    if USER_HEADER not in request.headers:
        log.debug("User header not present!")
        username = None
    else:
        user = request.headers[USER_HEADER]
        username = user.replace(USER_PREFIX, "")
        log.debug(
            f"User: '{username}' | Headers: '{USER_HEADER}' '{USER_PREFIX}'"
        )

    return username


def no_authentication(func):
    """
    This decorator will be used to disable the default authentication check
    for the decorated endpoint.
    """
    func.no_authentication = True
    return func


@bp.before_app_request
def check_authentication():
    """
    By default all the app's routes will be subject to authentication. If we
    want a function to not have authentication check then we can decorate it
    with the `no_authentication` decorator.
    """
    if config.dev_mode_enabled():
        log.debug("Skipping authentication check in development mode")
        return

    # If a function was decorated with `no_authentication` then we will skip
    # the authn check
    if request.endpoint and getattr(
        current_app.view_functions[request.endpoint],
        "no_authentication",
        False,
    ):
        # when no return value is specified the designated route function will
        # be called.
        return

    user = get_username()
    if user is None:
        # Return an unauthenticated response and don't call the route's
        # assigned function.
        raise Unauthorized("No user detected.")
    else:
        log.info(f"Handling request for user: {user}")
        return
