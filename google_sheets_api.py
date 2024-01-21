from dotenv import set_key, find_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os

def auth_user(scopes):
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", scopes)
    print(creds.valid)
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
def create_spreadsheet(title, creds):
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

def update_spreadsheet(values, creds):
  try:
    service = build("sheets", "v4", credentials=creds)
    body = {"values": values}
    result = (
       service.spreadsheets()
       .values()
       .update(
          spreadsheetId = get_spreadsheet_id(),
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
      
def get_spreadsheet_id():
  return os.getenv('SPREADSHEET_ID')