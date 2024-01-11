from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from warnings import filterwarnings
from datetime import datetime
import time
import os

from selenium.webdriver import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin

import re
from selenium.webdriver.support import expected_conditions as EC

import json
from dotenv import load_dotenv

load_dotenv()

filterwarnings("ignore")
time_str = datetime.today().strftime('%d_%m_%Y_%H_%M_%S')

def read_keywords(file_name):
    with open(file_name, 'r') as f:
        data = json.load(f)
    return data

def get_chrome_capabilities():
    caps = webdriver.DesiredCapabilities.CHROME
    caps['acceptSslCerts'] = True
    caps['acceptInsecureCerts'] = True
    opts = webdriver.ChromeOptions()
    caps.update(opts.to_capabilities())
    return caps

def check_content(keywords, search_text):
    keyword_copy = keywords.copy()
    for key in keyword_copy.keys():
        if key in search_text.lower():
            keyword_copy[key] = True
    return ", ".join(key for key, value in keyword_copy.items() if value == True)

def is_job_worth_to_save(item):
    forme_list = item.get("for_me_items").split(",")
    notforme_list = item.get("not_for_me_items").split(",")
    if any(word in forme_list for word in ["python", "django", "fastapi"]):
        return True
    elif any(word in notforme_list for word in ["spring", ".net", "c#"]):
        return False
    return True if len(forme_list)>1 else False

def scroll_down():
    header = driver.find_element(By.CLASS_NAME, "scaffold-layout__list-container")

    scroll_origin = ScrollOrigin.from_element(header, 50, 100) # Offset: right/down
    for i in range(5):
        ActionChains(driver).scroll_from_origin(scroll_origin, 0, 1000).perform() # Scroll down
        time.sleep(1)

chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

ITEM_LIST = []
driver = webdriver.Chrome(ChromeDriverManager().install())

driver.set_window_size(850, 960)
driver.set_window_position(0, 0)

KEYWORDS_INITIAL=read_keywords('keywords.json')
KEYWORDS = KEYWORDS_INITIAL
get_url = os.environ.get("JOB_SEARCH_URL")
# "https://www.linkedin.com/jobs/search/?currentJobId=3732882614&f_JT=F&f_WT=2&geoId=102105699&keywords=Python&location=T%C3%BCrkiye&origin=JOB_SEARCH_PAGE_SEARCH_BUTTON&sortBy=DD&start=0"
driver.get(get_url)

element = driver.find_element(By.XPATH, "//a[@data-tracking-control-name='public_jobs_nav-header-signin']")
driver.execute_script("arguments[0].click();", element)

time.sleep(10)

username = driver.find_element(By.ID, "username")
password = driver.find_element(By.ID, "password")

username.send_keys(os.environ.get("LINKEDIN_USERNAME"))
password.send_keys(os.environ.get("LINKEDIN_PASSWORD"))

element = driver.find_element(By.XPATH, "//button[@type='submit']")
time.sleep(30)
driver.execute_script("arguments[0].click();", element)
time.sleep(30)

# scroll_down()

PAGE_START_NUM=0
OLD_PAGE_NUM=0
PAGE_BREAK=int(os.environ.get("PAGE_BREAK", 5))

for search_index in range(PAGE_BREAK):
    if PAGE_START_NUM!=0: # if not fist time
        get_url = get_url.replace(f"&start={OLD_PAGE_NUM}", f"&start={PAGE_START_NUM}")
        driver.get(get_url)
        time.sleep(30)

    scroll_down()
    job_list = driver.find_elements(By.CLASS_NAME, "job-card-container__link,job-card-list__title")
    
    driver.execute_script("return document.body.scrollHeight")
    company, company_url = "", ""
    for k in job_list:
        name = k.text
        if len(name) > 0:
            driver.execute_script("arguments[0].click();", k)
            time.sleep(10)
            try:
                company_info = driver.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__primary-description-container")
                time.sleep(5)
                company_obj=company_info.find_element(By.CLASS_NAME, "app-aware-link")
                company_url = company_obj.get_attribute("href")
                company = company_obj.text
            except NoSuchElementException:
                continue # if there is no company name, its indivicual job description so you can pass this one
            job_details = driver.find_element(By.ID, "job-details").text
            time.sleep(5)
            job_type, about= "", ""
            try:
                job_type=driver.find_element(By.CLASS_NAME, "ui-label,ui-label--accent-3,text-body-small").text.split("\n")[0]
            except NoSuchElementException:
                pass
            try:
                about = driver.find_element(By.CLASS_NAME, "jobs-company__inline-information").text
            except NoSuchElementException:
                pass
            time.sleep(5)
            for_me = str(check_content(KEYWORDS.get("for_me"), job_details))
            not_for_me = str(check_content(KEYWORDS.get("not_for_me"), job_details))

            item={
                "job_name": name,
                "company": company, # selenium.common.exceptions.NoSuchElementException: Message: no such element: No node with given id found
                "about": about, # how many people works in the company which sector, short description about the company
                "job_type": job_type, # job_type='Uzaktan\nİş tercihleriniz eşleşiyor, işyeri türü Uzaktan.'
                "for_me_items": for_me,
                "not_for_me_items": not_for_me,
                "company_url": company_url,
                "job_url":k.get_attribute('href'),
              }
            print(item)
            try:
                save_button = driver.find_elements(By.CLASS_NAME, "jobs-save-button")[0]
            except IndexError:
                print(f"Already applied. job_name:{name} company:{company}")
                continue
            worth_to_save = is_job_worth_to_save(item)
            if worth_to_save and save_button and  "kaydet" in save_button.text.lower():
                time.sleep(5)
                driver.execute_script("arguments[0].click();", save_button)
                time.sleep(10)
                print(f"+++++ The job {name} saved. You can check saved job searchs in your profile.")
                ITEM_LIST.append(item)
                
                with open(f'results_{time_str}.json', 'w', encoding='utf-8') as f:
                    json.dump(ITEM_LIST, f, ensure_ascii=False, indent=4)
                time.sleep(10)
            elif worth_to_save and "kaydedildi" in save_button.text.lower():
                print(f">>>>> the job already saved. job_name:{name} company:{company}")
                ITEM_LIST.append(item)
                
                with open(f'results_{time_str}.json', 'w', encoding='utf-8') as f:
                    json.dump(ITEM_LIST, f, ensure_ascii=False, indent=4)
                time.sleep(10)
            else:
                print(f"----- The job {name} passed")
    OLD_PAGE_NUM=PAGE_START_NUM        
    PAGE_START_NUM+=25
