from celery import Celery
from celery.schedules import crontab
from job_search import main

import os
import io
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication


from dotenv import load_dotenv

load_dotenv()
app = Celery('tasks', broker='redis://redis:6379/0', backend='redis://redis:6379/0')

@app.task
def add(x, y):
    return x + y

@app.task
def run_job_search():
    # send_email_task_complete("Task started.", "The task started. This email has been sent by automatically.")
    result = main("docker")
    json_str = json.dumps(result, ensure_ascii=False, indent=4)
    send_email_task_complete("Task completed.", 
                             "The job search task has been completed successfully. This email has been sent by automatically.",
                             json_str)



def send_email_task_complete(subject, body, json_string=None):
    
    sender_email = os.environ.get("SENDER_EMAIL")
    receiver_email = os.environ.get("RECEIVER_EMAIL")

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    if json_string is not None:
        json_file = io.StringIO(json_string)
        json_file.seek(0)
        filename = "result.json"

        part = MIMEApplication(json_file.read(), Name=filename)
        part['Content-Disposition'] = f'attachment; filename="{filename}"'
        message.attach(part)

    try:
        server = smtplib.SMTP(os.environ.get("SMTP_SERVER"), os.environ.get("SMTP_PORT"))
        server.starttls()
        server.login(sender_email, os.environ.get("EMAIL_PASSWORD"))
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Error sending email: {e}")


app.conf.beat_schedule = {
    # 'execute-every-1-minute-on-friday': {
    #     'task': 'tasks.add',
    #     'schedule': crontab(minute='*/1', hour='8-23', day_of_week='fri'),
    #     'args': (1, 3),
    # },
    'execute-every-10-minute': {
        'task': 'tasks.add',
        'schedule': crontab(minute='*/10'),
        'args': (1, 3),
    },
    'execute-every-2-hours': {
        'task': 'tasks.run_job_search',
        'schedule': crontab(hour='*/5'),
    },
    # 'execute-every-60-minutes': {
    #     'task': 'tasks.run_job_search',
    #     'schedule': crontab(minute='*/60'),
    # },
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


add.delay(1,3)
run_job_search.delay()