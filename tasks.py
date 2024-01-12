from celery import Celery
from celery.schedules import crontab

app = Celery('tasks', broker='redis://redis:6379/0', backend='redis://redis:6379/0')

@app.task
def add(x, y):
    return x + y


app.conf.beat_schedule = {
    'add-every-specific-interval': {
        'task': 'tasks.add',
        'schedule': crontab(minute='*/10', hour='3,17,22', day_of_week='thu,fri'),
        'args': (1, 3),
    },
}