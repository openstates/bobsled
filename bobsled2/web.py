import datetime
import asyncio
import attr
from starlette.applications import Starlette
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from starlette.responses import JSONResponse
from starlette.endpoints import WebSocketEndpoint
import uvicorn
import jwt

from .base import Status
from .core import bobsled

templates = Jinja2Templates(directory='bobsled2/templates')

app = Starlette(debug=True)
app.mount('/static', StaticFiles(directory='static'), name='static')


@app.route("/")
@app.route('/task/{task_name}')
@app.route('/run/{run_id}')
async def index(request):
    return templates.TemplateResponse("base.html", {
        "request": request
    })


def _run2dict(run):
    run = attr.asdict(run)
    run['status'] = run["status"].name
    return run


@app.route('/api/login')
async def login(request):
    KEY_VALID_HOURS = 24*30
    try:
        username = request.query_params["username"]
        password = request.query_params["password"]
    except KeyError:
        return JSONResponse({
            "error": "must supply username and password"
        })
    user = bobsled.auth.check_login(username, password)
    if user:
        until = datetime.datetime.utcnow() + datetime.timedelta(hours=KEY_VALID_HOURS)
        return JSONResponse({
            "token": jwt.encode({
                "username": user.username,
                "permissions": user.permissions,
                "until": until.isoformat()
            },
                                key=bobsled.settings['secret_key']).decode()
        })
    else:
        return JSONResponse({
            "error": "invalid login"
        })


@app.route('/api/index')
async def api_index(request):
    return JSONResponse({
        'tasks': [attr.asdict(t) for t in bobsled.tasks.get_tasks()],
        'runs': [_run2dict(r) for r in await bobsled.run.get_runs(status=Status.Running)],
    })


@app.route('/api/task/{task_name}')
async def task_overview(request):
    task_name = request.path_params['task_name']
    task = bobsled.tasks.get_task(task_name)
    runs = await bobsled.run.get_runs(task_name=task_name, update_status=True)
    return JSONResponse({
        "task": attr.asdict(task),
        "runs": [_run2dict(r) for r in runs]
    })


@app.route('/api/task/{task_name}/run')
async def run_task(request):
    task_name = request.path_params['task_name']
    task = bobsled.tasks.get_task(task_name)
    run = await bobsled.run.run_task(task)
    return JSONResponse(_run2dict(run))


@app.route('/api/run/{run_id}')
async def run_detail(request):
    run_id = request.path_params['run_id']
    run = await bobsled.run.get_run(run_id)
    rundata = _run2dict(run)
    return JSONResponse(rundata)


@app.route('/api/run/{run_id}/stop')
async def stop_run(request):
    run_id = request.path_params['run_id']
    await bobsled.run.stop_run(run_id)
    return JSONResponse({})


@app.websocket_route('/ws/logs/{run_id}')
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
