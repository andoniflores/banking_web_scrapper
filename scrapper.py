from selenium import webdriver 
from bs4 import BeautifulSoup
import time
from dotenv import load_dotenv
import os

load_dotenv()
BANK_WEBSITE_URL=os.getenv('BANK_WEBSITE_URL')

options = webdriver.FirefoxOptions()
options.add_argument("--enable-javascript")

driver = webdriver.Firefox(options=options)
driver.get(BANK_WEBSITE_URL)

time.sleep(5)

html = driver.page_source
soup = BeautifulSoup(html)
print(soup.prettify())

driver.quit()