import scraper
import google_sheets_api
from dotenv import load_dotenv, set_key, find_dotenv
import os

load_dotenv()

driver = scraper.get_driver()
wait = scraper.get_driver_wait(driver)
scraper.login(driver, wait)
bank_data = scraper.get_bank_data(driver, wait)
driver.quit()

creds = google_sheets_api.auth_user(["https://www.googleapis.com/auth/spreadsheets"])
spreadsheet_id = os.getenv('SPREADSHEET_ID')
if not spreadsheet_id:
    spreadsheet_id = google_sheets_api.create_spreadsheet("Bank Statement")
    set_key(find_dotenv(), 'SPREADSHEET_ID', spreadsheet_id)

spreadsheet_headers = ["Date", "Description", "Amount Spent", "Amount Received", "Balance"]
spreadsheet_data = google_sheets_api.prepare_data_for_spreadsheet(bank_data, spreadsheet_headers)
result = google_sheets_api.update_spreadsheet(spreadsheet_data, creds)