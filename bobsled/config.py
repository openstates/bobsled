from __future__ import print_function
import yaml
import glob


def load_config():
    config = yaml.load(open('config.yaml'))

    config['tasks'] = []

    files = glob.glob('tasks/*.yml')
    for fn in files:
        with open(fn) as f:
            task = yaml.load(f)
            if isinstance(task['environment'], str):
                task['environment'] = config['environments'][task['environment']]
            config['tasks'].append(task)

    return config

