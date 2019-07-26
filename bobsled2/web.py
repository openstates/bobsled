import datetime
import asyncio
import attr
from starlette.applications import Starlette
from starlette.authentication import (
    AuthenticationBackend, AuthenticationError, SimpleUser, UnauthenticatedUser,
    AuthCredentials, requires
)
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from starlette.responses import JSONResponse, RedirectResponse
from starlette.endpoints import WebSocketEndpoint
from starlette.middleware.authentication import AuthenticationMiddleware
import uvicorn
import jwt

from .base import Status
from .core import bobsled


class JWTSessionAuthBackend(AuthenticationBackend):
    async def authenticate(self, request):
        jwt_token = request.cookies.get("jwt_token")

        if not jwt_token:
            print("auth null")
            return
        data = jwt.decode(jwt_token, bobsled.settings["secret_key"], algorithms=["HS256"])
        print("auth", data)

        return AuthCredentials(["authenticated"]), SimpleUser(data["username"])


templates = Jinja2Templates(directory='bobsled2/templates')

app = Starlette(debug=True)
app.add_middleware(AuthenticationMiddleware, backend=JWTSessionAuthBackend())
app.mount('/static', StaticFiles(directory='static'), name='static')

@app.route("/login", methods=["GET", "POST"])
async def login(request):
    KEY_VALID_HOURS = 24*30
    if request.method == "POST":
        form = await request.form()
        user = bobsled.auth.check_login(form["username"], form["password"])
        if user:
            resp = RedirectResponse("/", status_code=302)
            until = datetime.datetime.utcnow() + datetime.timedelta(hours=KEY_VALID_HOURS)
            token = jwt.encode({
                "username": user.username,
                "permissions": user.permissions,
                "until": until.isoformat()
            }, key=bobsled.settings['secret_key']).decode()
            resp.set_cookie("jwt_token", token)
            return resp

    # on get or after failed login
    return templates.TemplateResponse("login.html", {
        "request": request,
    })

@app.route("/")
@app.route('/task/{task_name}')
@app.route('/run/{run_id}')
@requires(['authenticated'])
async def index(request):
    return templates.TemplateResponse("base.html", {
        "request": request
    })


def _run2dict(run):
    run = attr.asdict(run)
    run['status'] = run["status"].name
    return run


@app.route('/api/index')
@requires(['authenticated'])
async def api_index(request):
    return JSONResponse({
        'tasks': [attr.asdict(t) for t in bobsled.tasks.get_tasks()],
        'runs': [_run2dict(r) for r in await bobsled.run.get_runs(status=Status.Running)],
    })


@app.route('/api/task/{task_name}')
@requires(['authenticated'])
async def task_overview(request):
    task_name = request.path_params['task_name']
    task = bobsled.tasks.get_task(task_name)
    runs = await bobsled.run.get_runs(task_name=task_name, update_status=True)
    return JSONResponse({
        "task": attr.asdict(task),
        "runs": [_run2dict(r) for r in runs]
    })


@app.route('/api/task/{task_name}/run')
@requires(['authenticated'])
async def run_task(request):
    task_name = request.path_params['task_name']
    task = bobsled.tasks.get_task(task_name)
    run = await bobsled.run.run_task(task)
    return JSONResponse(_run2dict(run))


@app.route('/api/run/{run_id}')
@requires(['authenticated'])
async def run_detail(request):
    run_id = request.path_params['run_id']
    run = await bobsled.run.get_run(run_id)
    rundata = _run2dict(run)
    return JSONResponse(rundata)


@app.route('/api/run/{run_id}/stop')
@requires(['authenticated'])
async def stop_run(request):
    run_id = request.path_params['run_id']
    await bobsled.run.stop_run(run_id)
    return JSONResponse({})


@app.websocket_route('/ws/logs/{run_id}')
@requires(['authenticated'])
async def websocket_endpoint(websocket):
    await websocket.accept()
    run_id = websocket.path_params["run_id"]
    while True:
        run = await bobsled.run.get_run(run_id)
        rundict = _run2dict(run)
        await websocket.send_json(rundict)
        if run.status not in (Status.Running, Status.Pending):
            break
        await asyncio.sleep(1)
    await websocket.close()


@app.on_event('startup')
async def initdb():
    await bobsled.run.persister.connect()


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000, lifespan="on")
