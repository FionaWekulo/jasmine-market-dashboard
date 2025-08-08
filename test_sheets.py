import os
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Load environment variables
load_dotenv()

# Set up Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SERVICE_ACCOUNT_FILE = 'credentials.json'

try:
    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=credentials)
    
    # Test reading from pharmacy sheet
    pharmacy_id = os.getenv('PHARMACY_SHEET_ID')
    
    # Get sheet data
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=pharmacy_id, range='A1:Z100').execute()
    values = result.get('values', [])
    
    print("✅ Google Sheets connection successful!")
    print(f"Found {len(values)} rows in pharmacy sheet")
    if values:
        print("Headers:", values[0])
        print(f"Response count: {len(values) - 1}")
    else:
        print("No data found - this is normal if no responses yet")
        
except Exception as e:
    print("❌ Error:", str(e))