from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from warnings import filterwarnings
from datetime import datetime
import time
import os
import argparse

from selenium.webdriver import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin

import re
from selenium.webdriver.support import expected_conditions as EC

import json
from dotenv import load_dotenv
import yaml


class LinkedInJobScraper:
    def __init__(self, worker_option):
        load_dotenv()
        filterwarnings("ignore")
        self.time_str = datetime.today().strftime('%d_%m_%Y_%H_%M_%S')
        self.KEYWORDS_INITIAL = self.read_keywords_yaml('keywords.yaml')
        self.KEYWORDS = self.KEYWORDS_INITIAL
        self.ITEM_LIST = []
        self.worker_option = worker_option
        self.driver = None

    def read_keywords_yaml(self, file_name):
        with open(file_name, 'r') as file:
            data = yaml.safe_load(file)

        for_me_list = data['for_me']
        not_for_me_list = data['not_for_me']

        keywords_json = {"for_me": {item: False for item in for_me_list},
                         "not_for_me": {item: False for item in not_for_me_list}}
        return keywords_json

    def get_chrome_capabilities(self):
        caps = webdriver.DesiredCapabilities.CHROME
        caps['acceptSslCerts'] = True
        caps['acceptInsecureCerts'] = True
        opts = webdriver.ChromeOptions()
        caps.update(opts.to_capabilities())
        return caps

    def check_content(self, keywords, search_text):
        keyword_copy = keywords.copy()
        for key in keyword_copy.keys():
            if key in search_text.lower():
                keyword_copy[key] = True
        return ",".join(key for key, value in keyword_copy.items() if value)

    def is_job_worth_to_save(self, item):
        forme_list = item.get("for_me_items").split(",")
        notforme_list = item.get("not_for_me_items").split(",")
        if any(word in forme_list for word in ["python", "django", "fastapi"]):
            return True
        elif any(word in notforme_list for word in ["java ", "spring", ".net", "c#", "php"]):
            return False
        return True if len(forme_list)>1 else False

    def scroll_down(self, driver):
        header = driver.find_element(By.CLASS_NAME, "scaffold-layout__list-container")
        scroll_origin = ScrollOrigin.from_element(header, 50, 100)  # Offset: right/down
        for i in range(5):
            ActionChains(driver).scroll_from_origin(scroll_origin, 0, 1000).perform()  # Scroll down
            time.sleep(1)

    def login(self):
        login_url = "https://www.linkedin.com/login"
        self.driver.get(login_url)
        time.sleep(10)

        username = self.driver.find_element(By.ID, "username")
        password = self.driver.find_element(By.ID, "password")

        username.send_keys(os.environ.get("LINKEDIN_USERNAME"))
        password.send_keys(os.environ.get("LINKEDIN_PASSWORD"))

        element = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        time.sleep(30)
        self.driver.execute_script("arguments[0].click();", element)

        check_error = self.driver.find_elements(By.CLASS_NAME, "form__label--error")
        if check_error:
            print('Your login informations are wrong. Check your login parameters in .env file and try again please')
            return False

        time.sleep(30)
        return True

    def prepare_driver_option(self):
        if self.worker_option == "docker":
            print("Driver is connecting to http://selenium-chrome:4444")
            options = webdriver.ChromeOptions()
            options.add_argument('--ignore-ssl-errors=yes')
            options.add_argument('--ignore-certificate-errors')
            self.driver = webdriver.Remote(command_executor='http://selenium-chrome:4444',
                                           desired_capabilities=DesiredCapabilities.CHROME, options=options)
        else:
            print("Local driver is running.")
            chrome_options = Options()
            chrome_options.add_experimental_option("detach", True)
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            self.driver = webdriver.Chrome(ChromeDriverManager().install())

        print(f'Driver connected. Browser options has been set as {self.worker_option}')
        self.driver.maximize_window()

        return f'Driver has been set as {self.worker_option}'

    def save_jobs_in_json(self):
        if self.worker_option == 'local':
            with open(f'results_{self.time_str}.json', 'w', encoding='utf-8') as f:
                json.dump(self.ITEM_LIST, f, ensure_ascii=False, indent=4)

    def get_jobs(self):
        PAGE_START_NUM, OLD_PAGE_NUM = 0, 0
        
        get_url = os.environ.get("JOB_SEARCH_URL")
        self.driver.get(get_url)
        time.sleep(30)
        
        PAGE_BREAK = int(os.environ.get("PAGE_BREAK", 5))
        for _ in range(PAGE_BREAK):
            if PAGE_START_NUM != 0:  # if not first time
                get_url = get_url.replace(f"&start={OLD_PAGE_NUM}", f"&start={PAGE_START_NUM}")
                self.driver.get(get_url)
                time.sleep(30)

            self.scroll_down(self.driver)
            job_list = self.driver.find_elements(By.CLASS_NAME, "job-card-container__link,job-card-list__title")

            self.driver.execute_script("return document.body.scrollHeight")
            company, company_url, job_url = "", "", ""
            for k in job_list:
                name = k.text
                if len(name)>0:
                    self.driver.execute_script("arguments[0].click();", k)
                    time.sleep(10)
                    try:
                        company_info = self.driver.find_element(By.CLASS_NAME,
                                                                "job-details-jobs-unified-top-card__primary-description-container")
                        time.sleep(5)
                        company_obj = company_info.find_element(By.CLASS_NAME, "app-aware-link")
                        company_url = company_obj.get_attribute("href")
                        company = company_obj.text
                    except NoSuchElementException:
                        continue

                    try:
                        job_url = k.get_attribute('href')
                    except NoSuchElementException:
                        continue
                    
                    job_details = self.driver.find_element(By.ID, "job-details").text
                    time.sleep(5)
                    job_type, about = "", ""
                    try:
                        job_type = self.driver.find_element(By.CLASS_NAME,
                                                            "ui-label,ui-label--accent-3,text-body-small").text.split(
                            "\n")[0]
                    except NoSuchElementException:
                        pass
                    try:
                        about = self.driver.find_element(By.CLASS_NAME, "jobs-company__inline-information").text
                    except NoSuchElementException:
                        pass
                    time.sleep(5)
                    for_me = str(self.check_content(self.KEYWORDS.get("for_me"), job_details))
                    not_for_me = str(self.check_content(self.KEYWORDS.get("not_for_me"), job_details))

                    item = {
                        "job_name": name,
                        "company": company,
                        "about": about,
                        "job_type": job_type,
                        "for_me_items": for_me,
                        "not_for_me_items": not_for_me,
                        "company_url": company_url,
                        "job_url": job_url,
                    }
                    print(json.dumps(item, indent=4))
                    try:
                        save_button = self.driver.find_elements(By.CLASS_NAME, "jobs-save-button")[0]
                    except IndexError:
                        print(f"Already applied. job_name:{name} company:{company}")
                        continue
                    worth_to_save = self.is_job_worth_to_save(item)
                    if worth_to_save and save_button and any(word in save_button.text.lower() for word in ["kaydet", "save"]):
                        time.sleep(5)
                        self.driver.execute_script("arguments[0].click();", save_button)
                        time.sleep(10)
                        print(f"+++++ The job {name} saved. You can check saved job searches in your profile.")
                        self.ITEM_LIST.append(item)

                        self.save_jobs_in_json()
                        time.sleep(10)
                    elif worth_to_save and any(word in save_button.text.lower() for word in ["kaydedildi", "saved"]):
                        print(f">>>>> the job already saved. job_name:{name} company:{company}")
                        self.ITEM_LIST.append(item)

                        self.save_jobs_in_json()
                        time.sleep(10)
                    else:
                        print(f"----- The job {name} passed")
            OLD_PAGE_NUM = PAGE_START_NUM
            PAGE_START_NUM += 25
        return self.ITEM_LIST

    def run(self):
        self.prepare_driver_option()
        self.login()
        return self.get_jobs()

def main(worker_option):
    linkedin_job_scraper = LinkedInJobScraper(worker_option=worker_option)
    return linkedin_job_scraper.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Arg parser for linkedin job search')
    parser.add_argument('-w', '--worker_option', help='Worker argument', required=True, default='docker', choices=['docker', 'local'])
    args = parser.parse_args()
    main(args.worker_option)
    print("Job Search Finished")
