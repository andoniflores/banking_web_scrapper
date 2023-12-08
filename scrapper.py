from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from bs4 import BeautifulSoup
import time
import dotenv
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
# print(decrypted_password)

BANK_WEBSITE_URL=os.getenv('BANK_WEBSITE_URL')
USERNAME=os.getenv('USERNAME')
PASSWORD=decrypted_password
REMEMBER_DEVICE_COOKIE=os.getenv('REMEMBER_DEVICE_COOKIE')

options = webdriver.FirefoxOptions()
options.add_argument("--enable-javascript")

driver = webdriver.Firefox(options=options)
driver.get(BANK_WEBSITE_URL)

# Wait for login fields to appear
wait = WebDriverWait(driver, timeout=5)
wait.until(lambda d : driver.find_element(By.ID, 'principal_name').is_displayed())
driver.add_cookie({'name': 'did', 'value': REMEMBER_DEVICE_COOKIE})

# Fill login fields
username = driver.find_element(By.ID, 'principal_name')
password = driver.find_element(By.ID, 'password')
username.send_keys(USERNAME)
password.send_keys(PASSWORD)
driver.find_element(By.ID, 'challenge-commit').click()

# Wait until remember device appears 
try:
    wait.until(lambda d : driver.find_element(By.ID, 'remember_accept').is_displayed())
    driver.find_element(By.ID, 'remember_accept').click()
    driver.find_element(By.ID, 'challenge-commit').click()

    # Ask user to input the email verification code
    email_verification_code = input('Please provide the verification code sent to your email:\n')

    # Fill the OTP fields
    verification_code_field = driver.find_element(By.ID, 'otp_email_answer')
    verification_code_field.send_keys(email_verification_code)
    driver.find_element(By.ID, 'challenge-commit').click()

    # Save 'did' cookie to skip 2FA next time
    remember_device_cookie = driver.get_cookie('did')
    print(remember_device_cookie)
    os.environ['REMEMBER_DEVICE_COOKIE'] = remember_device_cookie['value'] 
    dotenv.set_key(dotenv.find_dotenv(), 'REMEMBER_DEVICE_COOKIE', os.environ['REMEMBER_DEVICE_COOKIE'])
except:
    print("[INFO] Couldn't find remember device element, device is trusted")

# You are succesfully logged in to banking site!

# Find and click account summary
driver.find_element(By.XPATH, "//div[contains(@id, 'account_summary')]//a[contains(@href, '/account/')]").click()

html = driver.page_source
soup = BeautifulSoup(html, 'html5lib')
# print(soup.prettify())

time.sleep(10)

driver.quit()