import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import time
import os
import json
import random
# selenium libraries
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.webdriver.chrome.options import Options


def delay (x=random.randint(2, 3)):
    time.sleep(x)

def set_chrome_options():
    options = webdriver.ChromeOptions()
    # avoid using conventional viewports using selenium scripts
    options.add_argument("--window-size=1100,1000")
    # remove automation tags from the browser
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    # remove main extra parts metrics error
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # disable the browser notifications
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    prefs = {"profile.default_content_setting_values.notifications" : 2}
    options.add_experimental_option("prefs", prefs)
    # use User Agent at each request
    user_agents = pd.read_csv('chrome_user_agents.csv').user_agent
    user_agent = 'user-agent={}'.format(np.random.choice(user_agents))
    options.add_argument(user_agent)
    return options

def run_driver(base, options=True):
    # create chrome service
    service=Service(ChromeDriverManager().install())
    # create chrome driver
    if options:
        opts = set_chrome_options()
        driver = webdriver.Chrome(service=service, options=opts)
    else:
        driver = webdriver.Chrome(service=service)
    # go to website
    driver.get(base)
    return driver

def scroll_default(driver):
    previous_height = driver.execute_script('return document.body.scrollHeight')

    while True:
        driver.execute_script('window.scrollBy(0, document.body.scrollHeight)')
        delay(3)
        new_height = driver.execute_script('return document.body.scrollHeight')
        if new_height == previous_height:
            break
        previous_height = new_height
    return driver

def sign_in(path_to_user_info_file: str):
    # log in to linkedIn
    driver = run_driver('https://www.linkedin.com/login')

    file = open(path_to_user_info_file)
    lines = file.readlines()
    email = lines[0].strip()
    password = lines[1]
    # enter username
    elementID = driver.find_element_by_id('username')
    elementID.send_keys(email)
    # enter password
    elementID = driver.find_element_by_id('password')
    elementID.send_keys(password)

    elementID.submit()
    delay()
    return driver

def retreive_profile_links_from_company_url(url: str, driver):
    driver.get(url)
    delay()

    source = driver.page_source
    soup = BeautifulSoup(source, 'lxml')
    # get notifications number to be extracted while scraping other urls
    notification_number_tag = soup.find('title')
    notification_number = notification_number_tag.text.split(' ')[0]+' '
    # scroll to load all links
    driver = scroll_default(driver)
    links = []
    for link_tag in driver.find_elements(By.XPATH, '//a[@class = "ember-view link-without-visited-state"]'):
        link = link_tag.get_attribute('href')
        links.append(link)

    return links, notification_number

def retreive_data_from_each_link(links: list, key: str, driver, notification_number):
    info_path = 'overlay/contact-info/'
    emails = []
    numbers = []
    jobTitles = []
    fullNames = []
    keys = []

    for i, prof in enumerate(links):
        prof_url = prof + info_path
        print(f'URL {i}: {prof_url}')

        driver.get(prof_url)
        source = driver.page_source
        soup = BeautifulSoup(source, 'lxml')
        contact_info = soup.find_all('code')[-3]
        contact_info = json.loads(contact_info.contents[0])

        try:
            email = contact_info['data']['emailAddress']
        except:
            email = None
        
        
        try:
            if contact_info['data']['phoneNumbers'] == None:
                number = None
            else:
                number = contact_info['data']['phoneNumbers'][0]['number']
        except:
            number = None
        
        driver.get(prof)
        delay()
        source = driver.page_source
        soup = BeautifulSoup(source, 'lxml')
        
        try:
            jobTitle_tag = soup.find('div', {'class':'text-body-medium break-words'})
            jobTitle = jobTitle_tag.text.strip()
        except:
            jobTitle = None
        
        try:
            fullName_tag = soup.find('title')
            fullName = fullName_tag.text.split('|')[0].strip(notification_number).split(',')[0]
        except:
            fullName = None

        emails.append(email)
        numbers.append(number)
        jobTitles.append(jobTitle)
        fullNames.append(fullName)
        keys.append(key)
        print(fullName)

    print(len(fullNames), len(jobTitles), len(emails), len(numbers), len(links), len(keys))
    data = pd.DataFrame({
                'Full Name': fullNames,
                'Job Title':jobTitles,
                'Email': emails,
                'Number':numbers,
                'Link': links,
                'Keyword': keys})
    return data

