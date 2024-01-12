from celery import Celery
from celery.schedules import crontab
from main import run

app = Celery('tasks', broker='redis://redis:6379/0', backend='redis://redis:6379/0')

@app.task
def add(x, y):
    return x + y

@app.task
def run_job_search():
    return run()

app.conf.beat_schedule = {
    'execute-every-1-minute-on-friday': {
        'task': 'tasks.add',
        'schedule': crontab(minute='*/1', hour='8-23', day_of_week='fri'),
        'args': (1, 3),
    },
    'execute-every-15-minute-on-friday': {
        'task': 'tasks.run_job_search',
        'schedule': crontab(minute='*/15', hour='8-23', day_of_week='fri')
    },
}

# run_job_search.delay()