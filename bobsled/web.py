import os
import datetime
import asyncio
import attr
import zmq
import zmq.asyncio
from starlette.applications import Starlette
from starlette.authentication import (
    AuthenticationBackend,
    SimpleUser,
    AuthCredentials,
    requires,
)
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from starlette.responses import JSONResponse, RedirectResponse
from starlette.middleware.authentication import AuthenticationMiddleware
import uvicorn
import jwt

from .base import Status
from .exceptions import AlreadyRunning
from .core import bobsled


class JWTSessionAuthBackend(AuthenticationBackend):
    async def authenticate(self, request):
        jwt_token = request.cookies.get("jwt_token")

        if not jwt_token:
            return
        try:
            data = jwt.decode(
                jwt_token, bobsled.settings["secret_key"], algorithms=["HS256"]
            )
        except jwt.InvalidSignatureError:
            return

        return (
            AuthCredentials(["authenticated"] + data["permissions"]),
            SimpleUser(data["username"]),
        )


templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "templates")
)


app = Starlette(debug=True)
app.add_middleware(AuthenticationMiddleware, backend=JWTSessionAuthBackend())
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "static")),
    name="static",
)


@app.route("/login", methods=["GET", "POST"])
async def login(request):
    KEY_VALID_HOURS = 24 * 30
    if request.method == "POST":
        form = await request.form()
        logged_in = await bobsled.storage.check_password(
            form["username"], form["password"]
        )
        if logged_in:
            permissions = await bobsled.storage.get_permissions(form["username"])
            resp = RedirectResponse("/", status_code=302)
            until = datetime.datetime.utcnow() + datetime.timedelta(
                hours=KEY_VALID_HOURS
            )
            token = jwt.encode(
                {
                    "username": form["username"],
                    "permissions": permissions,
                    "until": until.isoformat(),
                },
                key=bobsled.settings["secret_key"],
            ).decode()
            resp.set_cookie("jwt_token", token)
            return resp

    # on get or after failed login
    return templates.TemplateResponse("login.html", {"request": request})


@app.route("/manage_users", methods=["GET", "POST"])
async def manage_users(request):
    errors = []
    message = ""
    usernames = await bobsled.storage.get_users()

    if usernames and "admin" not in request.auth.scopes:
        return RedirectResponse("/login")

    if request.method == "POST":
        form = await request.form()
        if not form.get("username"):
            errors.append("Username is required.")
        if not form.get("password"):
            errors.append("Password is required.")
        if form.get("password") != form.get("confirm_password"):
            errors.append("Passwords do not match.")
        if form.get("username") in usernames:
            errors.append("Username is already taken.")
        permissions = form.get("permissions", "").split(" ")
        if not errors:
            await bobsled.storage.set_user(
                form["username"], form["password"], permissions
            )
            usernames = await bobsled.storage.get_users()
            message = "Successfully created " + form["username"]

    return templates.TemplateResponse(
        "manage_users.html",
        {
            "request": request,
            "errors": errors,
            "message": message,
            "usernames": usernames,
        },
    )


@app.route("/")
@app.route("/latest_runs")
@app.route("/task/{task_name}")
@app.route("/run/{run_id}")
@requires(["authenticated"], redirect="login")
async def index(request):
    return templates.TemplateResponse("base.html", {"request": request})


def _run2dict(run):
    run = attr.asdict(run)
    run["status"] = run["status"].name
    return run


@app.route("/api/index")
@requires(["authenticated"], redirect="login")
async def api_index(request):
    tasks = [attr.asdict(t) for t in await bobsled.tasks.get_tasks()]
    results = await asyncio.gather(
        *[bobsled.run.get_runs(task_name=t["name"], latest=1) for t in tasks]
    )
    for task, latest_runs in zip(tasks, results):
        if latest_runs:
            task["latest_run"] = _run2dict(latest_runs[0])
        else:
            task["latest_run"] = None
    return JSONResponse(
        {
            "tasks": tasks,
            "runs": [
                _run2dict(r) for r in await bobsled.run.get_runs(status=Status.Running)
            ],
        }
    )


@app.route("/api/latest_runs")
@requires(["authenticated"], redirect="login")
async def latest_runs(request):
    return JSONResponse(
        {"runs": [_run2dict(r) for r in await bobsled.run.get_runs(latest=100)]}
    )


@app.route("/api/task/{task_name}")
@requires(["authenticated"], redirect="login")
async def task_overview(request):
    task_name = request.path_params["task_name"]
    task = await bobsled.tasks.get_task(task_name)
    runs = await bobsled.run.get_runs(
        task_name=task_name, update_status=True, latest=40
    )
    return JSONResponse(
        {"task": attr.asdict(task), "runs": [_run2dict(r) for r in runs]}
    )


@app.route("/api/task/{task_name}/run")
@requires(["authenticated"], redirect="login")
async def run_task(request):
    task_name = request.path_params["task_name"]
    if "admin" not in request.auth.scopes:
        return JSONResponse({"error": "Insufficient permissions."})
    task = await bobsled.tasks.get_task(task_name)
    try:
        run = await bobsled.run.run_task(task)
    except AlreadyRunning:
        return JSONResponse({"error": "Task was already running"})
    return JSONResponse(_run2dict(run))


@app.route("/api/run/{run_id}")
@requires(["authenticated"], redirect="login")
async def run_detail(request):
    run_id = request.path_params["run_id"]
    run = await bobsled.run.update_status(run_id, update_logs=True)
    rundata = _run2dict(run)
    return JSONResponse(rundata)


@app.route("/api/run/{run_id}/stop")
@requires(["authenticated"], redirect="login")
async def stop_run(request):
    run_id = request.path_params["run_id"]
    await bobsled.run.stop_run(run_id)
    return JSONResponse({})


@app.websocket_route("/ws/beat")
@requires(["authenticated"], redirect="login")
async def beat_websocket(websocket):
    context = zmq.asyncio.Context.instance()
    socket = context.socket(zmq.SUB)
    socket.connect("ipc:///tmp/bobsled-beat")
    socket.subscribe(b"")

    await websocket.accept()
    while True:
        msg = await socket.recv_string()
        await websocket.send_json({"msg": msg})
    await websocket.close()


@app.websocket_route("/ws/logs/{run_id}")
@requires(["authenticated"], redirect="login")
async def websocket_endpoint(websocket):
    await websocket.accept()
    run_id = websocket.path_params["run_id"]
    while True:
        run = await bobsled.run.update_status(run_id, update_logs=True)
        rundict = _run2dict(run)
        await websocket.send_json(rundict)
        if run.status not in (Status.Running, Status.Pending):
            break
        await asyncio.sleep(1)
    await websocket.close()


@app.on_event("startup")
async def init():
    await bobsled.initialize()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000, lifespan="on")
