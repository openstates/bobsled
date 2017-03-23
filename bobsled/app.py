from .status import render_runs, get_last_runs
from flask import Flask

app = Flask(__name__)


@app.route('/')
def show_entries():
    CHART_DAYS = 14
    runs = get_last_runs(CHART_DAYS)
    return render_runs(CHART_DAYS, runs)
