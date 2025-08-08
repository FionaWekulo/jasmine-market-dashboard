import os
import pandas as pd
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from anthropic import Anthropic
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize APIs
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SERVICE_ACCOUNT_FILE = 'credentials.json'

class JasmineAnalyzer:
    def __init__(self):
        self.credentials = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        self.service = build('sheets', 'v4', credentials=self.credentials)
        
        self.sheet_configs = {
            'customer': os.getenv('CUSTOMER_SHEET_ID'),
            'pharmacy': os.getenv('PHARMACY_SHEET_ID'),
            'insurance': os.getenv('INSURANCE_SHEET_ID'),
            'healthcare': os.getenv('HEALTHCARE_SHEET_ID')
        }
    
    def get_sheet_data(self, sheet_id):
        """Get data from a Google Sheet"""
        try:
            sheet = self.service.spreadsheets()
            result = sheet.values().get(spreadsheetId=sheet_id, range='A1:Z100').execute()
            values = result.get('values', [])
            return values
        except Exception as e:
            print(f"Error reading sheet {sheet_id}: {e}")
            return []
    
    def analyze_response(self, user_type, response_data):
        """Analyze a single response using Claude"""
        
        prompt = f"""
        Analyze this {user_type} response from our healthcare platform market research.
        
        Response data: {response_data}
        
        Please provide analysis in this exact JSON format:
        {{
            "pain_points": ["list of specific pain points mentioned"],
            "behaviors": ["current behaviors and habits"],
            "technology_comfort": "low/medium/high",
            "financial_concerns": ["any money-related issues"],
            "motivators": ["what would drive them to use our platform"],
            "sentiment": "positive/neutral/negative",
            "key_quotes": ["most important quotes from their stories"],
            "priority_score": 1-10
        }}
        
        Focus on extracting insights that will help us build the right features for our healthcare e-commerce platform in Kenya.
        """
        
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"Error analyzing response: {e}")
            return None

# Test it
if __name__ == "__main__":
    analyzer = JasmineAnalyzer()
    
    # Test with pharmacy data
    pharmacy_data = analyzer.get_sheet_data(analyzer.sheet_configs['pharmacy'])
    print(f"Pharmacy sheet has {len(pharmacy_data)} rows")
    
    if len(pharmacy_data) > 1:  # Has responses beyond header
        print("\nAnalyzing first pharmacy response...")
        analysis = analyzer.analyze_response('pharmacy', pharmacy_data[1])
        print("Analysis result:")
        print(analysis)
    else:
        print("No responses to analyze yet")