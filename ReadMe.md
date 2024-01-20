# Linkedin Job Search
Linkedin Job Search may have unnecessary keywords which I am not interested.
For example I search python jobs and I don't want to work on java. Many job results exist java so the job search operation may be wasting time. The python script generated to solve this problem.

## Tech Stack
Python, Selenium, Celery, Docker, Docker Compose

## environment variables
<p>Define your variables in .env file <br/>
USERNAME=Linkedin Username <br/>
PASSWORD=Linkedin Password <br/>
PAGE_BREAK=How many pages the script will work <br/>
JOB_SEARCH_URL=Which job search url will be run. be sure that the url should has &start=0 parameter

Email configurations for sending notifications upon completion of the Celery task <br/>
You will receive a mail with result.json in the attachments after the task finished. (Mail is only configured on docker) <br/>
SENDER_EMAIL="" <br/>
EMAIL_PASSWORD="" <br/>
RECEIVER_EMAIL="" <br/>
SMTP_SERVER="" # smtp.gmail.com if sender is gmail <br/>
SMTP_PORT=587 </p>

## keywords.yaml
<p>for_me=Which keywords you are interested in the job description. <br/>
not_for_me=The JD sometimes has unwanted keywords, if you are not interested you can eliminate them and continue to search for another one.</p>

## is_job_worth_to_save
Refactor the is_job_worth_to_save function as you wish, the function automatically saves the jobs for you.

## Run on Docker
<p>docker-compose up -d <br/>

Driver configs are different on local and docker. Remote connection performed on docker.
Selenium grid default port is 4444, you can check on vnc live screen while docker running. <br/>
http://localhost:4444/ui#/sessions
</p>

## Run on LOCAL prepare environment and run
<p>mkdir venv && cd venv <br/>
virtualenv . <br/>
cd .. <br/>
source venv/Scripts/activate <br/>
pip install -r requirements.txt <br/>
python job_search.py -w local</p>
