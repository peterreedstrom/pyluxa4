"""Luxafor server."""
from flask import Flask, jsonify, abort, make_response, request
from flask_httpauth import HTTPTokenAuth
from gevent.pywsgi import WSGIServer
from gevent.lock import BoundedSemaphore
import gevent
import time
import os
from . import scheduler
from . import usb
from . import common as cmn
from . import __meta__

sem = BoundedSemaphore(1)

app = Flask(__name__)
auth = HTTPTokenAuth('Bearer')
tokens = set()
luxafor = None
schedule = None
HOST = '0.0.0.0'
PORT = 5000


def get_api_ver_path():
    """Get the API path."""

    return '/pyluxa4/api/v%s.%s' % __meta__.__version_info__[:2]


@auth.verify_token
def verify_token(token):
    """Verify incoming token."""

    if token in tokens:
        return True
    return False


def color():
    """Set colors."""

    try:
        error = ''
        led = request.json.get("led", cmn.LED_ALL)
        cmn.is_int('led', led)
        color = request.json.get('color', '')
        cmn.is_str('color', color)
    except Exception as e:
        error = str(e)

    if not error:
        try:
            sem.acquire()
            luxafor.color(color, led=led)
            sem.release()
        except Exception as e:
            error = str(e)

    if error:
        abort(400, error)

    return jsonify(
        {
            "path": request.path,
            "status": 'success',
            "code": 200,
            "error": error
        }
    )


def fade():
    """Fade colors."""

    try:
        error = ''
        led = request.json.get("led", cmn.LED_ALL)
        cmn.is_int('led', led)
        color = request.json.get('color', '')
        cmn.is_str('color', color)
        speed = request.json.get('speed', 0)
        cmn.is_int('speed', speed)
    except Exception as e:
        error = str(e)

    if not error:
        try:
            sem.acquire()
            luxafor.fade(color, led=led, speed=speed)
            sem.release()
        except Exception as e:
            error = str(e)

    if error:
        abort(400, error)

    return jsonify(
        {
            "path": request.path,
            "status": 'success',
            "code": 200,
            "error": error
        }
    )


def strobe():
    """Strobe colors."""

    try:
        error = ''
        led = request.json.get("led", cmn.LED_ALL)
        cmn.is_int('led', led)
        color = request.json.get('color', '')
        cmn.is_str('color', color)
        speed = request.json.get('speed', 0)
        cmn.is_int('speed', speed)
        repeat = request.json.get('repeat', 0)
        cmn.is_int('repeat', repeat)
    except Exception as e:
        error = str(e)

    if not error:
        try:
            sem.acquire()
            luxafor.strobe(color, led=led, speed=speed, repeat=repeat)
            sem.release()
        except Exception as e:
            error = str(e)

    if error:
        abort(400, error)

    return jsonify(
        {
            "path": request.path,
            "status": 'success',
            "code": 200,
            "error": error
        }
    )


def wave():
    """Wave colors."""

    try:
        error = ''
        color = request.json.get('color', '')
        cmn.is_str('color', color)
        wave = request.json.get('wave', cmn.WAVE_SHORT)
        cmn.is_int('wave', wave)
        speed = request.json.get('speed', 0)
        cmn.is_int('speed', speed)
        repeat = request.json.get('repeat', 0)
        cmn.is_int('repeat', repeat)
    except Exception as e:
        error = str(e)

    if not error:
        try:
            sem.acquire()
            luxafor.wave(color, wave=wave, speed=speed, repeat=repeat)
            sem.release()
        except Exception as e:
            error = str(e)

    if error:
        abort(400, error)

    return jsonify(
        {
            "path": request.path,
            "status": 'success',
            "code": 200,
            "error": error
        }
    )


def pattern():
    """Set pattern."""

    try:
        error = ''
        pattern = request.json.get('pattern', 0)
        cmn.is_int('pattern', pattern)
        repeat = request.json.get('repeat', 0)
        cmn.is_int('repeat', repeat)
    except Exception as e:
        error = str(e)

    if not error:
        try:
            sem.acquire()
            luxafor.pattern(pattern, repeat=repeat)
            sem.release()
        except Exception as e:
            error = str(e)

    if error:
        abort(400, error)

    return jsonify(
        {
            "path": request.path,
            "status": 'success',
            "code": 200,
            "error": error
        }
    )


def off():
    """Set off."""

    error = ''
    try:
        sem.acquire()
        luxafor.off()
        sem.release()
    except Exception as e:
        error = str(e)

    if error:
        abort(400, error)

    return jsonify(
        {
            "path": request.path,
            "status": 'success',
            "code": 200,
            "error": error
        }
    )


def kill():
    """Kill."""

    try:
        error = ''
        http_server.close()
        http_server.stop(timeout=10)
    except Exception as e:
        error = str(e)

    if error:
        abort(400, error)

    return {
        "path": request.path,
        "status": 'success',
        "code": 200,
        "error": error
    }


def clear_schedule():
    """Clear schedule."""

    sem.acquire()
    schedule.clear_schedule()
    sem.release()

    return {
        "path": request.path,
        "status": 'success',
        'code': 200,
        'error': ''
    }


def setup_schedule():
    """Setup schedule."""

    sem.acquire()
    filename = request.json.get('file', '')
    append = request.json.get('append', False)
    if os.path.exists(filename) and os.path.isfile(filename):
        if not append:
            schedule.clear_schedule()
        err = schedule.read_schedule(filename)
    else:
        err = "The file '{}' does not exist".format(filename)
    sem.release()
    if err:
        abort(400, err)
    return {
        "path": request.path,
        "status": 'success',
        'code': 200,
        "error": err
    }


def check_schedule():
    """Check schedule in the background."""

    last = time.time()
    while True:
        if (time.time() - last) >= 10:
            sem.acquire()
            schedule.check_schedule()
            sem.release()
            last = time.time()
        gevent.sleep(30)


@app.route('/')
def index():
    """
    Print out some text for main page.

    This is really only here so we
    can quickly, visually check if server
    is running.
    """
    return "RESTful Luxafor server!"


@app.route('%s/command/<string:command>' % get_api_ver_path(), methods=['POST'])
@auth.login_required
def execute_command(command):
    """Executes a given command GET or POST command."""
    if request.method == 'POST':
        if command == 'color':
            results = color()
        elif command == 'fade':
            results = fade()
        elif command == 'strobe':
            results = strobe()
        elif command == 'wave':
            results = wave()
        elif command == 'pattern':
            results = pattern()
        elif command == 'off':
            results = off()
        elif command == 'kill':
            # Results won't make it back if successful
            results = kill()
        elif command == 'schedule':
            results = setup_schedule()
        elif command == 'clear-schedule':
            results = clear_schedule()
        else:
            abort(404)

    return results


@app.route('/pyluxa4/api/version', methods=['GET'])
def version():
    """Return version."""
    return jsonify(
        {
            "path": request.path,
            'status': 'success',
            'error': '',
            'version': __meta__.__version__,
            'version_path': get_api_ver_path()
        }
    )


@app.errorhandler(400)
def bad_request(error):
    """Return 400 error."""

    return make_response(
        jsonify(
            {
                "path": request.path,
                "status": "fail",
                "code": 400,
                "error": str(error)
            }
        ),
        400
    )


@app.errorhandler(404)
def not_found(error):
    """Return 404 error."""
    return make_response(
        jsonify(
            {
                "path": request.path,
                "status": "fail",
                "code": 404,
                "error": 'Request not found'
            }
        ),
        404
    )


@app.errorhandler(500)
def server_error(error):
    """Return 500 error."""
    return make_response(
        jsonify(
            {
                "path": request.path,
                "status": "fail",
                "code": 500,
                "error": 'Internal server error'
            }
        ),
        500
    )


def run(
    host=HOST, port=PORT, device_index=0, device_path=None, token=None, schedule_file=None,
    debug=False, **kwargs
):
    """Run server."""

    global luxafor
    global http_server
    global tokens
    global schedule

    with usb.Luxafor(device_index, device_path, token) as lf:
        luxafor = lf
        tokens = set([token])
        schedule = scheduler.Scheduler(luxafor)
        if schedule_file and os.path.exists(schedule_file) and os.path.isfile(schedule_file):
            err = schedule.read_schedule(schedule_file)
            if err:
                print(err)
        http_server = WSGIServer((host, port), app, **kwargs)
        serve = gevent.spawn(http_server.start)
        background = gevent.spawn(check_schedule)

        try:
            gevent.joinall([serve, background])
        except KeyboardInterrupt:
            pass
        print('Exiting')
