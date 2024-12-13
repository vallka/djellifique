import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

SPREADSHEET_ID = "1s3oOBQKGcSytND6xfbJW60DxD8CrlHFMtwHuIId2hmk"

def process_sheet(service,sheet_title,first_row):
    products = []
    if 'ID' in first_row and 'kg' in first_row:
        idx = first_row.index('ID')
        kgx = first_row.index('kg')
        print(f"***id and kg: {idx}: {kgx}")
        data_range_name = f"{sheet_title}!A2:M"

        data = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID, range=data_range_name
        ).execute()
        values = data.get('values', [])
        for row in values:
            if len(row)>idx and len(row)>kgx:
                print(row[idx],row[kgx])
                products.append({'ID':row[idx],'kg':row[kgx]})

    return products

def main():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    SERVICE_ACCOUNT_FILE = '.gcredentials.json'
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    try:
        products = []

        service = build("sheets", "v4", credentials=credentials)
        spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheets = spreadsheet.get('sheets', [])

        # Iterate through each sheet
        for sheet in sheets:
            # Each sheet object contains a 'properties' object with details.
            sheet_properties = sheet.get('properties', {})
            sheet_title = sheet_properties.get('title', 'Untitled')

            print(f"Sheet Title: {sheet_title}")
            range_name = f"{sheet_title}!1:1"

            # Retrieve the first row of the sheet
            result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
            values = result.get('values', [])
            if values:
                # values[0] represents the first row
                first_row = values[0]
                print(f"First row of {sheet_title}: {first_row}")

                products += process_sheet(service,sheet_title,first_row)
            else:
                print(f"No data found in the first row of {sheet_title}.")


        if products:
            print(products)

    except HttpError as err:
        print(err)


if __name__ == "__main__":
    main()