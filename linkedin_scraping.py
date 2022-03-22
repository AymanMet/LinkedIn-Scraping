"""
LinkedIn Scrapping using selenium, BeautifulSoup
"""
import pandas as pd
# import linkedIn utils
import linkedIn_utils as lu

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
    print(f'Keywords: {keywords}')
    return company_url, keywords

def main():
    company_url, keywords = asking_for_inputs()
    
    driver = lu.sign_in('user_info.txt')

    df = pd.DataFrame(columns=['Full Name', 'Job Title', 'Email', 'Number', 'Link', 'Keyword'])

    for key in keywords:
        key_tag = '?keywords='
        url = company_url + key_tag + key
        print(url)

        links, notification_number = lu.retreive_profile_links_from_company_url(url, driver)
        print(len(links))
        data = lu.retreive_data_from_each_link(links, key, driver, notification_number)
        
        df= df.append(data)

    company_name = company_url.split('/')[-3]

    df.to_csv('{}.csv'.format(company_name), index=False)

    driver.close()

if __name__ == "__main__":
    main()
    
