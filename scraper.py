from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from bs4 import BeautifulSoup
from dotenv import set_key, find_dotenv
import os
from cryptography.fernet import Fernet


def decrypt_password():
    # Load the encryption key
    with open("encryption_key.key", "rb") as key_file:
        key = key_file.read()

    # Get the encrypted password from .env
    encrypted_password = os.getenv("ENCRYPTED_PASSWORD")

    # Decrypt the password
    cipher_suite = Fernet(key)
    decrypted_password = cipher_suite \
        .decrypt(encrypted_password.encode()).decode()
    return decrypted_password


def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--enable-javascript")
    driver = webdriver.Chrome(options=options)
    driver.get(os.getenv('BANK_WEBSITE_URL'))
    return driver


def get_driver_wait(driver: webdriver.Chrome):
    return WebDriverWait(driver, timeout=5)


def login(driver: webdriver.Chrome, wait: WebDriverWait):
    wait.until(lambda d: driver.find_element(By.ID,
                                             'principal_name').is_displayed())
    driver.add_cookie({'name': 'did',
                       'value': os.getenv('REMEMBER_DEVICE_COOKIE')})

    # Fill login fields
    username = driver.find_element(By.ID, 'principal_name')
    password = driver.find_element(By.ID, 'password')
    username.send_keys(os.getenv('BANK_USERNAME'))
    password.send_keys(decrypt_password())
    driver.find_element(By.ID, 'challenge-commit').click()

    # Wait until remember device appears
    try:
        wait.until(lambda d: driver.
                   find_element(By.ID, 'remember_accept').is_displayed())
        driver.find_element(By.ID, 'remember_accept').click()
        driver.find_element(By.ID, 'challenge-commit').click()

        # Ask user to input the email verification code
        email_verification_code = input(
            'Please provide the verification code sent to your email:\n')

        # Fill the OTP fields
        verification_code_field = driver.find_element(By.ID,
                                                      'otp_email_answer')
        verification_code_field.send_keys(email_verification_code)
        driver.find_element(By.ID, 'challenge-commit').click()

        # Save 'did' cookie to skip 2FA next time
        remember_device_cookie = driver.get_cookie('did')
        os.environ['REMEMBER_DEVICE_COOKIE'] = remember_device_cookie['value']
        set_key(find_dotenv(), 'REMEMBER_DEVICE_COOKIE',
                os.environ['REMEMBER_DEVICE_COOKIE'])
    except Exception:
        print("[INFO] Couldn't find remember device element,"
              "device is trusted")


def get_bank_data(driver: webdriver.Chrome, wait: WebDriverWait):
    # Find and click account summary
    wait.until(
        lambda d: driver.find_element(
            By.XPATH,
            "//div[contains(@id, 'account_summary')]"
            "//a[contains(@href, '/account/')]"
        ).is_displayed()
    )
    driver.find_element(
        By.XPATH,
        "//div[contains(@id, 'account_summary')]"
        "//a[contains(@href, '/account/')]"
    ).click()

    html = driver.page_source
    soup = BeautifulSoup(html, 'html5lib')

    table = soup.find('table', attrs={'id': 'posted-table'})
    bank_data = []
    for row in table.findAll('tr'):
        row_class = row.attrs.get('class')
        if row_class is not None and "searchable" in row_class:
            data = {}
            data['date'] = row.find('td', title=True)['title']
            data['description'] = row.find('td', class_='cW cVT cUT')\
                .contents[0].text.strip()
            data['amount_spent'] = row.find('td', class_='cR cVT').text.strip()
            data['amount_received'] = row.find('td', class_='cR cVT')\
                .find_next_sibling().text.strip()
            data['balance'] = row.find('td', class_='cR cVT cUT').text.strip()
            bank_data.append(data)

    print(bank_data)
    return bank_data
