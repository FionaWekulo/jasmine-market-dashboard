import streamlit as st
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from anthropic import Anthropic
import json
from datetime import datetime
from collections import Counter

# Load environment variables (works both locally and on Streamlit Cloud)
load_dotenv()


def get_env_var(key):
    # For local development, just use environment variables
    return os.getenv(key)


st.set_page_config(
    page_title="Jasmine Pharmacy ",
    page_icon="💊",
    layout="wide"
)

st.title("💊 Exploring Digital Healthcare Market Research Dashboard")
st.markdown("### Real-time insights google form responses")
st.markdown("---")

# Initialize clients
@st.cache_resource
def init_clients():
    try:
        # Check if running on Streamlit Cloud (will have GOOGLE_CREDENTIALS_JSON env var)
        creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
        
        if creds_json:
            # Running on Streamlit Cloud
            import json
            credentials_info = json.loads(creds_json)
            credentials = Credentials.from_service_account_info(
                credentials_info,
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
        else:
            # Running locally - use credentials file
            credentials = Credentials.from_service_account_file(
                'credentials.json', 
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
        
        service = build('sheets', 'v4', credentials=credentials)
        anthropic_client = Anthropic(api_key=get_env_var("ANTHROPIC_API_KEY"))
        return service, anthropic_client
    except Exception as e:
        st.error(f"Setup error: {e}")
        return None, None
    
service, anthropic_client = init_clients()

sheet_configs = {
    'Customer': get_env_var('CUSTOMER_SHEET_ID'),
    'Pharmacy': get_env_var('PHARMACY_SHEET_ID'),
    'Insurance': get_env_var('INSURANCE_SHEET_ID'),
    'Healthcare Provider': get_env_var('HEALTHCARE_SHEET_ID')
}

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_all_responses():
    """Get responses from all sheets"""
    all_data = {}
    
    if not service:
        return {}
    
    for user_type, sheet_id in sheet_configs.items():
        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id, 
                range='A1:Z100'
            ).execute()
            values = result.get('values', [])
            
            if len(values) > 1:  # Has responses beyond header
                all_data[user_type] = {
                    'count': len(values) - 1,
                    'responses': values[1:],  # Skip header
                    'headers': values[0] if values else []
                }
            else:
                all_data[user_type] = {'count': 0, 'responses': [], 'headers': []}
                
        except Exception as e:
            st.error(f"Error loading {user_type} data: {e}")
            all_data[user_type] = {'count': 0, 'responses': [], 'headers': []}
    
    return all_data

def analyze_single_response(user_type, response_row):
    """Analyze a single response quickly"""
    if not anthropic_client or len(response_row) < 3:
        return None
    
    # Combine all responses into one text
    response_text = " | ".join([str(cell) for cell in response_row[2:] if cell])  # Skip timestamp and email
    
    prompt = f"""
    Analyze this {user_type} response from Kenyan healthcare platform research:
    
    "{response_text}"
    
    Return only valid JSON:
    {{
        "sentiment": "positive/neutral/negative",
        "main_pain_point": "biggest issue in 5-8 words",
        "tech_readiness": "low/medium/high",
        "priority_level": 1-10,
        "key_theme": "main theme in 2-3 words",
        "quick_insight": "one sentence insight"
    }}
    """
    
    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = response.content[0].text
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except Exception as e:
        st.error(f"Analysis error: {e}")
    
    return None

def generate_executive_summary(all_analyses_by_type):
    """Generate executive summary from all analyses"""
    if not anthropic_client:
        return None
    
    # Flatten all analyses
    all_insights = []
    for user_type, analyses in all_analyses_by_type.items():
        for analysis in analyses:
            if analysis:
                analysis['user_type'] = user_type
                all_insights.append(analysis)
    
    if not all_insights:
        return None
    
    prompt = f"""
    Based on these market research analyses from Kenya's healthcare platform study:
    
    {json.dumps(all_insights, indent=2)}
    
    Provide executive insights in this JSON format:
    {{
        "top_pain_points": ["top 5 pain points across all users"],
        "technology_readiness": "overall assessment with details",
        "market_opportunity": "key market opportunity identified",
        "priority_features": ["top 5 features to build first"],
        "user_sentiment": "overall sentiment with context",
        "key_risks": ["main risks to address"],
        "next_actions": ["top 3 recommended actions"],
        "business_impact": "potential business impact summary"
    }}
    
    Focus on actionable insights for building a healthcare e-commerce platform in Kenya.
    """
    
    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = response.content[0].text
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except Exception as e:
        st.error(f"Executive summary error: {e}")
    
    return None

# Get all data
with st.spinner("Loading data..."):
    all_responses = get_all_responses()

# Calculate totals
total_responses = sum([data['count'] for data in all_responses.values()])

# Overview metrics
st.markdown("### 📊 Response Overview")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Responses", total_responses)
with col2:
    st.metric("Customers", all_responses.get('Customer', {}).get('count', 0))
with col3:
    st.metric("Pharmacies", all_responses.get('Pharmacy', {}).get('count', 0))
with col4:
    st.metric("Insurance", all_responses.get('Insurance', {}).get('count', 0))
with col5:
    st.metric("Healthcare Providers", all_responses.get('Healthcare Provider', {}).get('count', 0))

# Visual charts
if total_responses > 0:
    st.markdown("### 📈 Response Distribution")
    
    # Pie chart
    counts = [all_responses[ut]['count'] for ut in sheet_configs.keys()]
    fig = px.pie(
        values=counts,
        names=list(sheet_configs.keys()),
        title="Responses by User Type"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    
    # Executive Summary Section
if total_responses > 0:
    st.markdown("### 🎯 Executive Summary")
    
    # Collect all analyses first
    all_analyses_by_type = {}
    
    with st.spinner("Generating executive insights..."):
        for user_type in sheet_configs.keys():
            user_data = all_responses.get(user_type, {})
            if user_data.get('count', 0) > 0:
                analyses = []
                responses_to_analyze = user_data.get('responses', [])[:3]  # Limit for speed
                
                for response_row in responses_to_analyze:
                    analysis = analyze_single_response(user_type, response_row)
                    if analysis:
                        analyses.append(analysis)
                
                all_analyses_by_type[user_type] = analyses
    
    # Generate executive summary
    executive_summary = generate_executive_summary(all_analyses_by_type)
    
    if executive_summary:
        # Create executive dashboard
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🚨 TOP PAIN POINTS:**")
            for pain_point in executive_summary.get('top_pain_points', []):
                st.write(f"• {pain_point}")
            
            st.markdown("**📱 TECHNOLOGY READINESS:**")
            st.write(executive_summary.get('technology_readiness', 'Assessment pending'))
            
            st.markdown("**💰 MARKET OPPORTUNITY:**")
            st.write(executive_summary.get('market_opportunity', 'Analysis in progress'))
        
        with col2:
            st.markdown("**⭐ PRIORITY FEATURES:**")
            for feature in executive_summary.get('priority_features', []):
                st.write(f"• {feature}")
            
            st.markdown("**😊 USER SENTIMENT:**")
            st.write(executive_summary.get('user_sentiment', 'Analysis pending'))
            
            st.markdown("**⚠️ KEY RISKS:**")
            for risk in executive_summary.get('key_risks', []):
                st.write(f"• {risk}")
        
        # Next actions box
        st.markdown("**🎯 RECOMMENDED NEXT ACTIONS:**")
        next_actions_col1, next_actions_col2, next_actions_col3 = st.columns(3)
        
        actions = executive_summary.get('next_actions', [])
        if len(actions) >= 1:
            with next_actions_col1:
                st.success(f"1. {actions[0]}")
        if len(actions) >= 2:
            with next_actions_col2:
                st.info(f"2. {actions[1]}")
        if len(actions) >= 3:
            with next_actions_col3:
                st.warning(f"3. {actions[2]}")
        
        # Business impact highlight
        if executive_summary.get('business_impact'):
            st.markdown("**💼 BUSINESS IMPACT:**")
            st.info(executive_summary.get('business_impact'))
    
    else:
        st.info("Executive summary will appear once we have more response data to analyze.")
    
    st.markdown("---")
    
    # Detailed analysis section
    st.markdown("### 🔍 Detailed Insights")
    
    # Create tabs for each user type
    user_tabs = st.tabs(list(sheet_configs.keys()))
    
    for i, user_type in enumerate(sheet_configs.keys()):
        with user_tabs[i]:
            user_data = all_responses.get(user_type, {})
            response_count = user_data.get('count', 0)
            
            if response_count > 0:
                st.write(f"**{response_count} {user_type} response(s)**")
                
                # Analyze responses
                with st.spinner(f"Analyzing {user_type} responses..."):
                    analyses = []
                    
                    # Analyze up to 5 most recent responses
                    responses_to_analyze = user_data.get('responses', [])[:5]
                    
                    for response_row in responses_to_analyze:
                        analysis = analyze_single_response(user_type, response_row)
                        if analysis:
                            analyses.append(analysis)
                
                if analyses:
                    # Create metrics from analyses
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write("**Sentiment:**")
                        sentiments = [a['sentiment'] for a in analyses]
                        sentiment_counts = Counter(sentiments)
                        for sentiment, count in sentiment_counts.items():
                            percentage = (count / len(sentiments)) * 100
                            color = "🟢" if sentiment == "positive" else "🟡" if sentiment == "neutral" else "🔴"
                            st.write(f"{color} {sentiment.title()}: {percentage:.0f}%")
                    
                    with col2:
                        st.write("**Technology Readiness:**")
                        tech_levels = [a['tech_readiness'] for a in analyses]
                        tech_counts = Counter(tech_levels)
                        for level, count in tech_counts.items():
                            percentage = (count / len(tech_levels)) * 100
                            icon = "🚀" if level == "high" else "📱" if level == "medium" else "📞"
                            st.write(f"{icon} {level.title()}: {percentage:.0f}%")
                    
                    with col3:
                        priorities = [a['priority_level'] for a in analyses]
                        avg_priority = sum(priorities) / len(priorities)
                        st.metric("Priority Score", f"{avg_priority:.1f}/10")
                    
                    # Show key insights
                    st.write("**Key Pain Points:**")
                    for analysis in analyses:
                        st.write(f"• {analysis['main_pain_point']}")
                    
                    st.write("**Quick Insights:**")
                    for analysis in analyses:
                        st.write(f"💡 {analysis['quick_insight']}")
                else:
                    st.info("Analysis in progress... Please refresh in a moment.")
            else:
                st.info(f"No {user_type.lower()} responses yet.")
                st.write("Share the survey link to collect responses!")

else:
    st.info("No responses collected yet. Share your survey links!")

# Survey links
st.markdown("---")
st.markdown("### 📝 Survey Links - Share These!")

col1, col2 = st.columns(2)
with col1:
    st.markdown("**🧑‍⚕️ Customer Survey:**")
    st.code("https://forms.gle/6Zi2WWTZZwk9zUQm9")
    st.markdown("**💊 Pharmacy Survey:**")
    st.code("https://forms.gle/1RQySvVR5ijEPUCj7")

with col2:
    st.markdown("**🏢 Insurance Survey:**")
    st.code("https://forms.gle/AgdN4LNpiRjoRp3dA")
    st.markdown("**👨‍⚕️ Healthcare Provider Survey:**")
    st.code("https://forms.gle/pQ3fiBDpqeesRTCD8")

# Refresh button
if st.button("🔄 Refresh All Data"):
    st.cache_data.clear()
    st.rerun()

st.markdown(f"---")
st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Auto-refreshes every 5 minutes*")