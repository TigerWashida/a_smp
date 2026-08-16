import json
from pathlib import Path
from datetime import date

study_goals = []
tasks = []

DATA_DIR = Path(__file__).parent.parent / "data"
#print(DATA_DIR)
DATA_DIR.mkdir(exist_ok=True)

GOALS_FILE = DATA_DIR / "study_goals.json"

TASKS_FILE = DATA_DIR / "tasks.json"



def ensure_file_exists(path):
    if not path.exists():
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4)


ensure_file_exists(GOALS_FILE)
ensure_file_exists(TASKS_FILE)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, default=str)

# store study_goals
study_goals = load_json(GOALS_FILE)

tasks = load_json(TASKS_FILE)

def load_study_goals():
    return load_json(GOALS_FILE)

def load_tasks():
    return load_json(TASKS_FILE)

def save_study_goals(study_goals):
    save_json(GOALS_FILE, study_goals)

def save_tasks(tasks):
    save_json(TASKS_FILE, tasks)