from celery import Celery
from celery.schedules import crontab
from job_search import main

app = Celery('tasks', broker='redis://redis:6379/0', backend='redis://redis:6379/0')

@app.task
def add(x, y):
    return x + y

@app.task
def run_job_search():
    return main('docker')

app.conf.beat_schedule = {
    # 'execute-every-1-minute-on-friday': {
    #     'task': 'tasks.add',
    #     'schedule': crontab(minute='*/1', hour='8-23', day_of_week='fri'),
    #     'args': (1, 3),
    # },
    'execute-every-minute': {
        'task': 'tasks.add',
        'schedule': crontab(minute='*/1'),
        'args': (1, 3),
    },
    'execute-every-3-hours': {
        'task': 'tasks.run_job_search',
        'schedule': crontab(minute=0, hour='*/3'),
    },
    # 'execute-everyday-per-3-hours': {
    #     'task': 'tasks.run_job_search',
    #     'schedule': crontab(hour='8-23/3') # everyday per 3 hours between 8am-23pm.  8 AM, 11 AM, 2 PM, 5 PM, 8 PM, and 11 PM
    # },
    # 'run-every-15-minutes': {
    #     'task': 'tasks.run_job_search',
    #     'schedule': crontab(minute='*/15'), # every 15 minutes
    # },
    
    # 'execute-every-15-minute-on-friday': {
    #     'task': 'tasks.run_job_search',
    #     'schedule': crontab(minute='*/15', hour='8-23', day_of_week='fri')
    # },
    # 'every-three-hours-on-weekdays': {
    #     'task': 'tasks.your_task_name',
    #     'schedule': crontab(hour='8-23/3', day_of_week='mon-fri'), # (Monday to Friday) between 8 AM and 11 PM  every three hours, 8-11-14-17-20-23
    # },
}
