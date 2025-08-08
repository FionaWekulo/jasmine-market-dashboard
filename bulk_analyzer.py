import os
import pandas as pd
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from anthropic import Anthropic
import json
from datetime import datetime
from collections import Counter, defaultdict

# Load environment variables
load_dotenv()

# Initialize APIs
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class BulkAnalyzer:
    def __init__(self):
        # Previous initialization code...
        self.credentials = Credentials.from_service_account_file(
            'credentials.json', scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
        self.service = build('sheets', 'v4', credentials=self.credentials)
        
        self.sheet_configs = {
            'customer': os.getenv('CUSTOMER_SHEET_ID'),
            'pharmacy': os.getenv('PHARMACY_SHEET_ID'),
            'insurance': os.getenv('INSURANCE_SHEET_ID'),
            'healthcare': os.getenv('HEALTHCARE_SHEET_ID')
        }
        
        # Store all analyses
        self.all_analyses = {}
    
    def get_sheet_data(self, sheet_id):
        """Get data from a Google Sheet"""
        try:
            sheet = self.service.spreadsheets()
            result = sheet.values().get(spreadsheetId=sheet_id, range='A1:Z1000').execute()
            values = result.get('values', [])
            return values
        except Exception as e:
            print(f"Error reading sheet: {e}")
            return []
    
    def analyze_all_responses(self):
        """Analyze all responses from all sheets"""
        
        for user_type, sheet_id in self.sheet_configs.items():
            print(f"\n📋 Analyzing {user_type} responses...")
            
            data = self.get_sheet_data(sheet_id)
            if len(data) <= 1:  # Only headers or empty
                print(f"No responses in {user_type} sheet yet")
                continue
                
            # Analyze each response
            analyses = []
            for i, row in enumerate(data[1:], 1):  # Skip header
                if len(row) > 2:  # Has actual responses
                    print(f"  Analyzing {user_type} response {i}...")
                    analysis = self.analyze_single_response(user_type, row)
                    if analysis:
                        analyses.append(analysis)
            
            self.all_analyses[user_type] = analyses
            print(f"✅ Completed {len(analyses)} {user_type} analyses")
    
    def analyze_single_response(self, user_type, response_data):
        """Analyze a single response"""
        prompt = f"""
        Analyze this {user_type} response from our Kenyan healthcare platform research.
        
        Response: {response_data}
        
        Return ONLY valid JSON in this format:
        {{
            "pain_points": ["specific pain points"],
            "behaviors": ["current behaviors"],
            "technology_comfort": "low/medium/high",
            "financial_concerns": ["money issues"],
            "motivators": ["what would drive adoption"],
            "sentiment": "positive/neutral/negative",
            "key_quotes": ["important quotes"],
            "priority_score": 1-10,
            "themes": ["main themes from story"]
        }}
        """
        
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse JSON from response
            analysis_text = response.content[0].text
            # Extract JSON from response (might have extra text)
            start = analysis_text.find('{')
            end = analysis_text.rfind('}') + 1
            json_str = analysis_text[start:end]
            
            return json.loads(json_str)
        except Exception as e:
            print(f"Error analyzing response: {e}")
            return None
    
    def generate_aggregate_insights(self):
        """Generate insights across all user types"""
        
        aggregate_prompt = f"""
        Based on these analyses from our Kenyan healthcare platform research:
        
        {json.dumps(self.all_analyses, indent=2)}
        
        Provide executive insights in JSON format:
        {{
            "executive_summary": "2-3 sentence overview",
            "top_pain_points": ["top 5 pain points across all users"],
            "technology_readiness": "overall assessment",
            "market_opportunity": "key opportunities identified",
            "priority_features": ["top 5 features to build first"],
            "user_sentiment": "overall sentiment across groups",
            "key_risks": ["main risks to address"],
            "next_actions": ["recommended next steps"]
        }}
        """
        
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1500,
                messages=[{"role": "user", "content": aggregate_prompt}]
            )
            
            analysis_text = response.content[0].text
            start = analysis_text.find('{')
            end = analysis_text.rfind('}') + 1
            json_str = analysis_text[start:end]
            
            return json.loads(json_str)
        except Exception as e:
            print(f"Error generating aggregate insights: {e}")
            return None

# Test it
if __name__ == "__main__":
    analyzer = BulkAnalyzer()
    
    print("🚀 Starting bulk analysis...")
    analyzer.analyze_all_responses()
    
    print("\n📊 Generating aggregate insights...")
    insights = analyzer.generate_aggregate_insights()
    
    if insights:
        print("\n" + "="*50)
        print("EXECUTIVE INSIGHTS")
        print("="*50)
        for key, value in insights.items():
            print(f"\n{key.upper().replace('_', ' ')}:")
            if isinstance(value, list):
                for item in value:
                    print(f"  • {item}")
            else:
                print(f"  {value}")