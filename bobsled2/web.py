from starlette.applications import Starlette
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
import uvicorn

from .base import Status
from bobsled2.core import bobsled

templates = Jinja2Templates(directory='bobsled2/templates')

app = Starlette(debug=True)
app.mount('/static', StaticFiles(directory='bobsled2/static'), name='static')


@app.route('/')
async def homepage(request):
    return templates.TemplateResponse('index.html', {
        'request': request,
        'tasks': bobsled.tasks.get_tasks(),
        'runs': bobsled.run.get_runs(Status.Running),
    })


@app.route('/t/{task_name}')
async def task_overview(request):
    task_name = request.path_params['task_name']
    task = bobsled.tasks.get_task(task_name)
    return templates.TemplateResponse('task_overview.html', {
        'request': request,
        "task": task,
    })


@app.route('/t/{task_name}/run')
async def task_overview(request):
    task_name = request.path_params['task_name']
    task = bobsled.tasks.get_task(task_name)
    bobsled.run.run_task(task)


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
