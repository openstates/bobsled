import attr
from starlette.applications import Starlette
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from starlette.responses import JSONResponse
from starlette.endpoints import WebSocketEndpoint
import uvicorn

from .base import Status
from bobsled2.core import bobsled

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


@app.route('/api/index')
async def api_index(request):
    return JSONResponse({
        'tasks': [attr.asdict(t) for t in bobsled.tasks.get_tasks()],
        'runs': [_run2dict(r) for r in bobsled.run.get_runs(status=Status.Running)],
    })


@app.route('/api/task/{task_name}')
async def task_overview(request):
    task_name = request.path_params['task_name']
    task = bobsled.tasks.get_task(task_name)
    runs = bobsled.run.get_runs(task_name=task_name, update_status=True)
    return JSONResponse({
        "task": attr.asdict(task),
        "runs": [_run2dict(r) for r in runs]
    })


@app.route('/api/task/{task_name}/run')
async def run_task(request):
    task_name = request.path_params['task_name']
    task = bobsled.tasks.get_task(task_name)
    run = bobsled.run.run_task(task)
    return JSONResponse(_run2dict(run))


@app.route('/api/run/{run_id}')
async def run_detail(request):
    run_id = request.path_params['run_id']
    run = bobsled.run.get_run(run_id)
    rundata = _run2dict(run)
    return JSONResponse(rundata)


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
