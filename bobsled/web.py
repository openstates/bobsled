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
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.responses import JSONResponse, RedirectResponse
from starlette.routing import Route, WebSocketRoute, Mount
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
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
            AuthCredentials(["authenticated"] + (data["permissions"] or [])),
            SimpleUser(data["username"]),
        )


templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "templates")
)


async def logout(request):
    r = RedirectResponse("/login", status_code=302)
    r.delete_cookie("jwt_token")
    return r


async def login(request):
    KEY_VALID_HOURS = 24 * 30
    if request.method == "POST":
        form = await request.form()
        logged_in = await bobsled.storage.check_password(
            form["username"], form["password"]
        )
        if logged_in:
            user = await bobsled.storage.get_user(form["username"])
            permissions = user.permissions
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


async def admin_view(request):
    errors = []
    message = ""
    users = await bobsled.storage.get_users()

    # if there are no users, let someone in to make one
    if users and "admin" not in request.auth.scopes:
        return RedirectResponse("/login")

    if request.method == "POST":
        form = await request.form()
        if not form.get("username"):
            errors.append("Username is required.")
        if not form.get("password"):
            errors.append("Password is required.")
        if form.get("password") != form.get("confirm_password"):
            errors.append("Passwords do not match.")
        if form.get("username") in [u.username for u in users]:
            errors.append("Username is already taken.")

        permissions = []
        if form.get("admin"):
            permissions.append("admin")

        if not errors:
            await bobsled.storage.set_user(
                form["username"], form["password"], permissions
            )
            users = await bobsled.storage.get_users()
            message = "Successfully created " + form["username"]

    return templates.TemplateResponse(
        "admin.html",
        {"request": request, "errors": errors, "message": message, "users": users},
    )


@requires(["authenticated"], redirect="login")
async def index(request):
    return templates.TemplateResponse("base.html", {"request": request})


def _parse_time(time):
    return datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f")


def _run2dict(run):
    run = attr.asdict(run)
    run["status"] = run["status"].name
    if run["end"]:
        tdelta = _parse_time(run["end"]) - _parse_time(run["start"])
        hour, rem = divmod(tdelta.seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        run["duration"] = f"{hour}:{minutes:02d}:{seconds:02d}"
    else:
        run["duration"] = ""
    return run


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


@requires(["authenticated"], redirect="login")
async def latest_runs(request):
    return JSONResponse(
        {"runs": [_run2dict(r) for r in await bobsled.run.get_runs(latest=100)]}
    )


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


@requires(["authenticated"], redirect="login")
async def run_detail(request):
    run_id = request.path_params["run_id"]
    run = await bobsled.run.update_status(run_id, update_logs=True)
    rundata = _run2dict(run)
    return JSONResponse(rundata)


@requires(["authenticated"], redirect="login")
async def stop_run(request):
    run_id = request.path_params["run_id"]
    await bobsled.run.stop_run(run_id)
    return JSONResponse({})


@requires(["authenticated", "admin"], redirect="login")
async def update_tasks(request):
    tasks = [attr.asdict(t) for t in await bobsled.refresh_tasks()]
    return JSONResponse({"tasks": tasks})


@requires(["authenticated"], redirect="login")
async def beat_websocket(websocket):
    hostname = os.environ.get("BOBSLED_BEAT_HOSTNAME", "beat")
    port = os.environ.get("BOBSLED_BEAT_PORT", "1988")
    context = zmq.asyncio.Context.instance()
    socket = context.socket(zmq.SUB)
    socket.connect(f"tcp://{hostname}:{port}")
    socket.subscribe(b"")

    await websocket.accept()
    while True:
        msg = await socket.recv_string()
        await websocket.send_json({"msg": msg})
    await websocket.close()


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


app = Starlette(
    debug=True,
    routes=[
        # non-React HTML views
        Route("/logout", logout),
        Route("/login", login, methods=["GET", "POST"]),
        Route("/admin", admin_view, methods=["GET", "POST"]),
        # React
        Route("/", index),
        Route("/latest_runs", index),
        Route("/task/{task_name}", index),
        Route("/run/{run_id}", index),
        # API
        Route("/api/index", api_index),
        Route("/api/latest_runs", latest_runs),
        Route("/api/task/{task_name}", task_overview),
        Route("/api/task/{task_name}/run", run_task, methods=["POST"]),
        Route("/api/run/{run_id}", run_detail),
        Route("/api/run/{run_id}/stop", stop_run),
        Route("/api/update_tasks", update_tasks, methods=["POST"]),
        # websockets
        WebSocketRoute("/ws/beat", beat_websocket),
        WebSocketRoute("/ws/logs/{run_id}", websocket_endpoint),
        # static files
        Mount(
            "/static",
            StaticFiles(
                directory=os.path.join(os.path.dirname(__file__), "..", "static")
            ),
            name="static",
        ),
    ],
    middleware=[Middleware(AuthenticationMiddleware, backend=JWTSessionAuthBackend())],
    on_startup=[bobsled.initialize],
)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000, lifespan="on")
