"""
LinkedIn Scrapping using selenium, BeautifulSoup
"""
import pandas as pd
import requests
from selenium import webdriver
from bs4 import BeautifulSoup
import json
import time


def asking_for_inputs():
    welcome_message = ("""Welcome to LinkedIn scraper!
    This app takes a company LinkedIn url and scrapes data of
    people working there while filtering them by keywords\n""")
    print(welcome_message)

    url = input('So please, enter the link of the company\n')
    if url[-8:] == '/people/':
        company_url = url
    else:
        company_url = url + 'people/'

    keywords = []
    while True:
        keyword = input('Enter one keyword or enter no to start searching\n').lower()
        if keyword == 'no':
            break
        keywords.append(keyword)
    print(keywords)
    return company_url, keywords

def sign_in(path_to_user_info_file: str):
    driver = webdriver.Chrome('chromedriver.exe')
    driver.get('https://www.linkedin.com/login')

    file = open(path_to_user_info_file)
    lines = file.readlines()
    email = lines[0].strip()
    password = lines[1]

    elementID = driver.find_element_by_id('username')
    elementID.send_keys(email)

    elementID = driver.find_element_by_id('password')
    elementID.send_keys(password)

    elementID.submit()
    time.sleep(3)
    return driver

def retreive_profile_links_from_company_url(url: str, driver):
    driver.get(url)
    time.sleep(3)

    source = driver.page_source
    soup = BeautifulSoup(source, 'lxml')
    companyNumber_tag = soup.find('title')
    companyNumber = companyNumber_tag.text.split(' ')[0]+' '

    previous_height = driver.execute_script('return document.body.scrollHeight')

    while True:
        driver.execute_script('window.scrollBy(0, document.body.scrollHeight)')
        time.sleep(3)
        
        new_height = driver.execute_script('return document.body.scrollHeight')
        if new_height == previous_height:
            break
        previous_height = new_height

    links = []
    for link_tag in driver.find_elements_by_xpath('//a[@class = "ember-view link-without-visited-state"]'):
        link = link_tag.get_attribute('href')
        links.append(link)

    return links, companyNumber

def retreive_data_from_each_link(links: list, key: str, driver, companyNumber):
    info_path = 'detail/contact-info/'
    emails = []
    numbers = []
    jobTitles = []
    fullNames = []

    for prof in links:
        prof_url = prof + info_path
        print(prof_url)
        
        driver.get(prof_url)
        source = driver.page_source
        soup = BeautifulSoup(source, 'lxml')
        contact_info = soup.find_all('code')[-3]
        contact_info = json.loads(contact_info.contents[0])

        try:
            email = contact_info['data']['emailAddress']
        except:
            email = None
        emails.append(email)
        
        try:
            if contact_info['data']['phoneNumbers'] == None:
                number = None
            else:
                number = contact_info['data']['phoneNumbers'][0]['number']
        except:
            number = None
        numbers.append(number)
        
        driver.get(prof)
        time.sleep(2)
        source = driver.page_source
        soup = BeautifulSoup(source, 'lxml')
        
        try:
            jobTitle_tag = soup.find('div', {'class':'text-body-medium break-words'})
            jobTitle = jobTitle_tag.text.strip()
        except:
            jobTitle = None
        jobTitles.append(jobTitle)
        
        try:
            fullName_tag = soup.find('title')
            fullName = fullName_tag.text.split('|')[0].strip(companyNumber)
        except:
            fullName = None
        fullNames.append(fullName)
        print(fullName)
        
    keys = []
    keys.append(key)
    keys = len(links) * keys
    print(len(fullNames), len(jobTitles), len(emails), len(numbers), len(links), len(keys))
    data = pd.DataFrame({'fullName': fullNames, 'jobTitle': jobTitles, 'email': emails, 'number': numbers, 'link': links, 'key': keys})
    return data




if __name__ == "__main__":

    company_url, keywords = asking_for_inputs()

    driver = sign_in('user_info.txt')

    df = pd.DataFrame(columns=['fullName', 'jobTitle', 'email', 'number', 'link', 'key'])
    
    for key in keywords:
        key_tag = '?keywords='
        url = company_url + key_tag + key
        print(url)

        links, comp_no = retreive_profile_links_from_company_url(url, driver)
        print(len(links))
        data = retreive_data_from_each_link(links, key, driver, comp_no)
        
        df= df.append(data)

    company_name = company_url.split('/')[-3]

    df.to_csv('{}.csv'.format(company_name), index=False)

    driver.close()
