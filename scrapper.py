from httplib2 import Credentials
from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from bs4 import BeautifulSoup
from dotenv import load_dotenv, set_key, find_dotenv
import os

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


from cryptography.fernet import Fernet

def auth_user(scopes):
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", scopes)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", scopes
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())
  return creds

def create_spreadsheet(title):
  try:
    service = build("sheets", "v4", credentials=creds)
    spreadsheet = {"properties": {"title": title}}
    spreadsheet = (
        service.spreadsheets()
        .create(body=spreadsheet, fields="spreadsheetId")
        .execute()
    )
    set_key(find_dotenv(), 'SPREADSHEET_ID', spreadsheet.get("spreadsheetId"))
    print(f"Spreadsheet ID: {(spreadsheet.get('spreadsheetId'))}")
    return spreadsheet.get("spreadsheetId")
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error

def update_spreadsheet(values):
  try:
    service = build("sheets", "v4", credentials=creds)
    body = {"values": values}
    result = (
       service.spreadsheets()
       .values()
       .update(
          spreadsheetId = spreadsheet_id,
          range = f'A1:E{len(values)}',
          valueInputOption = 'USER_ENTERED',
          body=body,
       )
       .execute()
    )
    print(f"{result.get('updatedCells')} cells updated.")
    return result 
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error

def prepare_data_for_spreadsheet(data, spreadsheet_headers):
  spreadsheet_data = []
  spreadsheet_data.append(spreadsheet_headers)
  for bank_entry in data:
    data_array = []
    data_array.append(bank_entry['date'])
    data_array.append(bank_entry['description'])
    data_array.append(bank_entry['amount_spent'])
    data_array.append(bank_entry['amount_received'])
    data_array.append(bank_entry['balance'])
    spreadsheet_data.append(data_array)
  
  return spreadsheet_data
      

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

BANK_USERNAME=os.getenv('BANK_USERNAME')
BANK_WEBSITE_URL=os.getenv('BANK_WEBSITE_URL')
PASSWORD=decrypted_password
REMEMBER_DEVICE_COOKIE=os.getenv('REMEMBER_DEVICE_COOKIE')

options = webdriver.ChromeOptions()
options.add_argument("--enable-javascript")

driver = webdriver.Chrome(options=options)
driver.get(BANK_WEBSITE_URL)

# Wait for login fields to appear
wait = WebDriverWait(driver, timeout=5)
wait.until(lambda d : driver.find_element(By.ID, 'principal_name').is_displayed())
driver.add_cookie({'name': 'did', 'value': REMEMBER_DEVICE_COOKIE})

# Fill login fields
username = driver.find_element(By.ID, 'principal_name')
password = driver.find_element(By.ID, 'password')
username.send_keys(BANK_USERNAME)
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
    os.environ['REMEMBER_DEVICE_COOKIE'] = remember_device_cookie['value'] 
    set_key(find_dotenv(), 'REMEMBER_DEVICE_COOKIE', os.environ['REMEMBER_DEVICE_COOKIE'])
except:
    print("[INFO] Couldn't find remember device element, device is trusted")

# You are succesfully logged in to banking site!

# Find and click account summary
wait.until(lambda d: driver.find_element(By.XPATH, "//div[contains(@id, 'account_summary')]//a[contains(@href, '/account/')]").is_displayed())
driver.find_element(By.XPATH, "//div[contains(@id, 'account_summary')]//a[contains(@href, '/account/')]").click()

html = driver.page_source
soup = BeautifulSoup(html, 'html5lib')

table = soup.find('table', attrs = {'id':'posted-table'})
bank_data = []
for row in table.findAll('tr'):
    clss = row.attrs.get('class')
    if clss is not None and "searchable" in clss:
        data = {}
        data['date'] = row.find('td', title=True)['title']
        data['description'] = row.find('td', class_='cW cVT cUT').contents[0].text.strip()
        data['amount_spent'] = row.find('td', class_='cR cVT').text.strip()
        data['amount_received'] = row.find('td', class_='cR cVT').find_next_sibling().text.strip()
        data['balance'] = row.find('td', class_='cR cVT cUT').text.strip()
        bank_data.append(data)

print(bank_data)
driver.quit()

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

spreadsheet_id =os.getenv('SPREADSHEET_ID')
creds = auth_user(SCOPES)

if not spreadsheet_id:
  spreadsheet_id = create_spreadsheet("Bank Statement")

spreadsheet_headers = ["Date", "Description", "Amount Spent", "Amount Received", "Balance"]
result = update_spreadsheet(prepare_data_for_spreadsheet(bank_data, spreadsheet_headers))