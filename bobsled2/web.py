import attr
from starlette.applications import Starlette
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from starlette.responses import RedirectResponse, JSONResponse
import uvicorn

from .base import Status
from bobsled2.core import bobsled

templates = Jinja2Templates(directory='bobsled2/templates')

app = Starlette(debug=True)
app.mount('/static', StaticFiles(directory='static'), name='static')

@app.route("/")
@app.route('/task/{task_name}')
async def index(request):
    return templates.TemplateResponse("base.html", {
        "request": request
    })


@app.route('/api/index')
async def api_index(request):
    return JSONResponse({
        'tasks': [attr.asdict(t) for t in bobsled.tasks.get_tasks()],
        'runs': [attr.asdict(r) for r in bobsled.run.get_runs(status=Status.Running)],
    })


@app.route('/api/task/{task_name}')
async def task_overview(request):
    task_name = request.path_params['task_name']
    task = bobsled.tasks.get_task(task_name)
    return JSONResponse({
        "task": attr.asdict(task),
        "runs": [attr.asdict(r) for r in bobsled.run.get_runs(task_name=task_name)]
    })


@app.route('/task/{task_name}/run')
async def run_task(request):
    task_name = request.path_params['task_name']
    task = bobsled.tasks.get_task(task_name)
    bobsled.run.run_task(task)
    return RedirectResponse(f"/task/{task_name}")


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
