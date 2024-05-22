from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import os
import time
from search_terms import search_terms_dict
import logging
import smtplib
from dotenv import load_dotenv
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


def configure():
    load_dotenv()


configure()

# EMAIL CREDENTIALS
incoming_email = os.getenv('incoming_email')
password = os.getenv('password')
outgoing_email = os.getenv('outgoing_email')

chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option('detach', True)

driver = webdriver.Chrome(options=chrome_options)

driver.get('https://www.cdkeys.com/pc')

search_box = driver.find_element(By.XPATH, "//input[@class='ais-SearchBox-input']")

notification_message = ''

for item in search_terms_dict:
    logging.warning('scraping new item')
    search_box = driver.find_element(By.XPATH, "//input[@class='ais-SearchBox-input']")
    search_box.send_keys(item['search term'])

    # TODO add implicit/explicit wait
    time.sleep(5)

    container = driver.find_element(By.ID, "algolia-right-container")
    results = container.find_elements(By.XPATH, ".//div[@class='result-sub-content']")

    for result in results:

        # GET ALL SEARCH RESULTS
        try:
            title = result.find_element(By.CLASS_NAME, "result-title").text

            # TODO CHECK IF IN STOCK FUNCTIONALITY
            # CHECK IF IN STOCK
            # logging.warning('Checking if in stock')
            # in_stock_button = result.find_element(By.XPATH, ".//div[@class='stock unavailable']")
            # print(in_stock_button.text)

            url = result.find_element(By.XPATH, "./h3/a").get_attribute("href")
            price = result.find_element(By.XPATH, ".//span[@itemprop='lowPrice']").text

            # FORMAT PRICE
            price = price.replace('RSD', '').replace(',', '')
            price = int(price)

            # CHECK IF ALL KEYWORDS IN TITLE
            # TODO improve code so the search works with both roman and arabic numerals
            keywords = item['search term'].split(' ')
            keywords_present = True
            for keyword in keywords:
                if keyword.upper() not in title:
                    keywords_present = False
                else:
                    pass

            # CHECK PRICE
            if price <= item['cutoff price']:
                price_lower = True
            else:
                price_lower = False

            # CHECK IF DLC
            if 'DLC' in title:
                if item['dlc']:
                    dlc_condition = True
                else:
                    dlc_condition = False
            else:
                if item['dlc']:
                    dlc_condition = False
                else:
                    dlc_condition = True

            # CHECK PLATFORM
            if item['platform'].upper() in title:
                platform_condition = True
            else:
                platform_condition = False

            # TODO filter out results such as pre-order bonus content

            # CHECK ALL CONDITIONS
            # logging.warning(f'checking conditions for +++++++++++++ {title}')
            # logging.warning(f'keywords condition is {keywords_present}')
            # logging.warning(f'price condition is {price_lower}')
            # logging.warning(f'dlc condition is {dlc_condition}')
            # logging.warning(f'platform condition is {platform_condition}')

            if keywords_present and price_lower and dlc_condition and platform_condition:
                notification_message += f'{title} is available for {price}RSD at {url}\n\n'

        except NoSuchElementException:
            pass

    # CLEAR THE SEARCH BAR
    search_box.send_keys(Keys.CONTROL + "a")
    search_box.send_keys(Keys.DELETE)

driver.quit()

# SEND THE NOTIFICATION EMAIL
if notification_message != '':
    with smtplib.SMTP('smtp.gmail.com', port=587) as connection:
        connection.starttls()
        connection.login(user=outgoing_email, password=password)
        connection.sendmail(
            from_addr=outgoing_email,
            to_addrs=incoming_email,
            msg='Subject: There are items available at CDKeys\n\n'
                f'{notification_message}'
        )
