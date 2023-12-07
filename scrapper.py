from selenium import webdriver 
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
from dotenv import load_dotenv
import os

from cryptography.fernet import Fernet

# Load environment variables from .env file
load_dotenv()

# Load the encryption key
with open("encryption_key.key", "rb") as key_file:
    key = key_file.read()

# Get the encrypted password from .env
encrypted_password = os.getenv("ENCRYPTED_PASSWORD")

# Decrypt the password
cipher_suite = Fernet(key)
decrypted_password = cipher_suite.decrypt(encrypted_password.encode()).decode()

# Now, you can use the decrypted password in your code
print(decrypted_password)

BANK_WEBSITE_URL=os.getenv('BANK_WEBSITE_URL')
USERNAME=os.getenv('USERNAME')
PASSWORD=decrypted_password

options = webdriver.FirefoxOptions()
options.add_argument("--enable-javascript")

driver = webdriver.Firefox(options=options)
driver.get(BANK_WEBSITE_URL)

time.sleep(5)

username = driver.find_element(By.ID, 'principal_name')
password = driver.find_element(By.ID, 'password')
username.send_keys(USERNAME)
password.send_keys(PASSWORD)
driver.find_element(By.ID, 'challenge-commit').click()

html = driver.page_source
soup = BeautifulSoup(html)
print(soup.prettify())

time.sleep(10)

driver.quit()