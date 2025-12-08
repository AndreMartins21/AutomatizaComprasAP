import gspread
import os 
from google.oauth2.service_account import Credentials


def get_connection_with_google_sheet(
    service_account_json_path: str = "service_account.json"
) -> gspread.Client:
    creds: Credentials = Credentials.from_service_account_file(
        service_account_json_path,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

    client: gspread.Client = gspread.authorize(creds)

    return client


def get_google_sheet_object(url: str = None) -> gspread.Spreadsheet:
    if not url:
        try:
            url = os.environ['URL_SHEET']
        except:
            raise Exception(f'[-] Não foi possível encontrar a url "{url}"')
        
    client = get_connection_with_google_sheet()

    sheet: gspread.Spreadsheet = client.open_by_url(url)

    return sheet


if __name__ == '__main__':
    sheet = get_google_sheet_object()
    new_sheet = sheet.add_worksheet(title="testando", rows=100, cols=20)

    print("New sheet created:", new_sheet.title)