import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime
from collections import Counter, defaultdict
import re

# Load environment variables
load_dotenv()

def get_env_var(key):
    return os.getenv(key)

st.set_page_config(
    page_title="Jasmine Pharmacy",
    page_icon="💊",
    layout="wide"
)

st.title("💊 Exploring Digital Healthcare Market Research Dashboard")
st.markdown("### Rule based insights google form responses")
st.markdown("---")

class RuleBasedAnalyzer:
    def __init__(self):
        # Define keyword patterns for each insight bucket
        self.pain_point_keywords = {
            'stock_issues': ['out of stock', 'shortage', 'unavailable', 'no stock', 'stockout', 'sold out'],
            'insurance_delays': ['insurance delay', 'claim delay', 'waiting', 'slow process', 'took long', 'insurance problem'],
            'payment_issues': ['payment problem', 'cash only', 'no mpesa', 'expensive', 'cost too much', 'cant afford'],
            'technology_problems': ['system down', 'not working', 'failed', 'crashed', 'slow app', 'tech problem'],
            'delivery_issues': ['delivery delay', 'no delivery', 'transport problem', 'far', 'distance', 'cant deliver'],
            'prescription_problems': ['prescription problem', 'doctor form', 'need stamp', 'signed form', 'prescription required']
        }
        
        self.behavior_keywords = {
            'cash_payment': ['cash', 'pay cash', 'physical money', 'notes', 'coins'],
            'online_usage': ['online', 'app', 'website', 'digital', 'phone app', 'mobile'],
            'pharmacy_visit': ['went to pharmacy', 'visited', 'physical store', 'in person', 'walked to'],
            'family_sharing': ['family', 'wife', 'husband', 'children', 'share phone', 'family member'],
            'mpesa_usage': ['mpesa', 'm-pesa', 'mobile money', 'paybill', 'till number']
        }
        
        self.tech_comfort_keywords = {
            'high_comfort': ['easy to use', 'comfortable with tech', 'good with apps', 'love technology', 'tech savvy', 'digital banking'],
            'medium_comfort': ['sometimes use', 'learning', 'okay with apps', 'basic use', 'getting used to'],
            'low_comfort': ['difficult', 'hard to use', 'prefer person', 'not comfortable', 'avoid technology', 'confusing']
        }
        
        self.sentiment_keywords = {
            'positive': ['good', 'great', 'excellent', 'happy', 'satisfied', 'easy', 'fast', 'convenient', 'love', 'perfect'],
            'negative': ['bad', 'terrible', 'frustrated', 'angry', 'slow', 'difficult', 'expensive', 'problem', 'hate', 'awful'],
            'neutral': ['okay', 'normal', 'usual', 'standard', 'average', 'fine']
        }

    def analyze_response_row(self, user_type, response_row):
        """Analyze a single response row"""
        if len(response_row) < 3:
            return None
        
        # Combine all text responses (skip timestamp and email)
        full_text = " ".join([str(cell).lower() for cell in response_row[2:] if cell and str(cell).strip() != '']).strip()
        
        if not full_text or full_text in ['', 'nan', 'none', 'test']:
            return None
        
        analysis = {
            'user_type': user_type,
            'response_length': len(full_text),
            'pain_points': self._extract_pain_points(full_text),
            'behaviors': self._extract_behaviors(full_text),
            'tech_comfort': self._assess_tech_comfort(full_text),
            'sentiment': self._analyze_sentiment(full_text),
            'key_themes': self._extract_themes(full_text),
            'financials': self._extract_financial_mentions(full_text),
            'priority_score': self._calculate_priority(full_text),
            'word_count': len(full_text.split()),
            'sample_quote': self._extract_best_quote(full_text)
        }
        
        return analysis
    
    def _extract_pain_points(self, text):
        """Extract pain points from text"""
        found_pain_points = []
        
        for category, keywords in self.pain_point_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    found_pain_points.append(category.replace('_', ' ').title())
                    break
        
        # Additional pattern matching
        if re.search(r'(problem|issue|difficult|hard|trouble|frustrat)', text):
            if 'General Issues' not in found_pain_points:
                found_pain_points.append("General Issues")
        
        return found_pain_points[:3]  # Limit to top 3
    
    def _extract_behaviors(self, text):
        """Extract behaviors from text"""
        found_behaviors = []
        
        for category, keywords in self.behavior_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    found_behaviors.append(category.replace('_', ' ').title())
                    break
        
        return found_behaviors[:3]
    
    def _assess_tech_comfort(self, text):
        """Assess technology comfort level"""
        high_score = sum(1 for keyword in self.tech_comfort_keywords['high_comfort'] if keyword in text)
        medium_score = sum(1 for keyword in self.tech_comfort_keywords['medium_comfort'] if keyword in text)
        low_score = sum(1 for keyword in self.tech_comfort_keywords['low_comfort'] if keyword in text)
        
        if high_score >= max(medium_score, low_score) and high_score > 0:
            return "High"
        elif medium_score >= low_score and medium_score > 0:
            return "Medium"
        elif low_score > 0:
            return "Low"
        else:
            return "Medium"  # Default
    
    def _analyze_sentiment(self, text):
        """Analyze sentiment without AI"""
        pos_score = sum(1 for keyword in self.sentiment_keywords['positive'] if keyword in text)
        neg_score = sum(1 for keyword in self.sentiment_keywords['negative'] if keyword in text)
        
        if pos_score > neg_score:
            return "Positive"
        elif neg_score > pos_score:
            return "Negative"
        else:
            return "Neutral"
    
    def _extract_themes(self, text):
        """Extract key themes"""
        themes = []
        
        # Insurance theme
        if any(word in text for word in ['insurance', 'claim', 'cover', 'nhif']):
            themes.append("Insurance")
        
        # Technology theme
        if any(word in text for word in ['app', 'online', 'digital', 'technology', 'mobile']):
            themes.append("Technology")
        
        # Cost theme
        if any(word in text for word in ['expensive', 'cost', 'price', 'money', 'afford']):
            themes.append("Cost")
        
        # Delivery theme
        if any(word in text for word in ['delivery', 'transport', 'bring', 'send', 'deliver']):
            themes.append("Delivery")
            
        # Stock theme
        if any(word in text for word in ['stock', 'available', 'shortage', 'supply']):
            themes.append("Stock Management")
        
        return themes[:3]
    
    def _extract_financial_mentions(self, text):
        """Extract financial concerns"""
        financial_issues = []
        
        if any(word in text for word in ['expensive', 'cost', 'afford', 'money', 'price']):
            financial_issues.append("Cost Concerns")
        
        if any(word in text for word in ['cash flow', 'payment delay', 'credit', 'debt']):
            financial_issues.append("Cash Flow Issues")
            
        if any(word in text for word in ['budget', 'savings', 'cheap', 'discount']):
            financial_issues.append("Budget Constraints")
        
        return financial_issues
    
    def _calculate_priority(self, text):
        """Calculate priority score 1-10 based on urgency indicators"""
        urgency_words = ['urgent', 'emergency', 'critical', 'immediate', 'asap', 'quickly']
        problem_words = ['problem', 'issue', 'difficult', 'impossible', 'frustrating']
        
        score = 5  # Base score
        
        # Increase for urgency
        for word in urgency_words:
            if word in text:
                score += 2
                break
        
        # Increase for problems
        problem_count = sum(1 for word in problem_words if word in text)
        score += min(problem_count, 2)
        
        # Increase for length (more detailed = higher priority)
        if len(text) > 200:
            score += 1
        elif len(text) > 100:
            score += 0.5
        
        return min(10, max(1, int(score)))
    
    def _extract_best_quote(self, text):
        """Extract a meaningful quote from the response"""
        sentences = re.split(r'[.!?]+', text)
        
        # Find sentence with most keywords
        best_sentence = ""
        max_keywords = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # Minimum length
                keyword_count = 0
                
                # Count pain point keywords
                for keywords in self.pain_point_keywords.values():
                    keyword_count += sum(1 for keyword in keywords if keyword in sentence)
                
                if keyword_count > max_keywords:
                    max_keywords = keyword_count
                    best_sentence = sentence[:100] + "..." if len(sentence) > 100 else sentence
        
        return best_sentence if best_sentence else text[:50] + "..."

    def generate_summary(self, all_analyses):
        """Generate executive summary from analyses"""
        if not all_analyses:
            return None
        
        # Filter out None analyses
        valid_analyses = [a for a in all_analyses if a]
        if not valid_analyses:
            return None
        
        # Aggregate data
        all_pain_points = []
        all_behaviors = []
        all_sentiments = []
        all_tech_comfort = []
        all_themes = []
        all_priorities = []
        
        for analysis in valid_analyses:
            all_pain_points.extend(analysis.get('pain_points', []))
            all_behaviors.extend(analysis.get('behaviors', []))
            all_sentiments.append(analysis.get('sentiment', 'Neutral'))
            all_tech_comfort.append(analysis.get('tech_comfort', 'Medium'))
            all_themes.extend(analysis.get('key_themes', []))
            all_priorities.append(analysis.get('priority_score', 5))
        
        # Count occurrences
        pain_point_counts = Counter(all_pain_points)
        behavior_counts = Counter(all_behaviors)
        sentiment_counts = Counter(all_sentiments)
        tech_counts = Counter(all_tech_comfort)
        theme_counts = Counter(all_themes)
        
        # Generate insights
        avg_priority = sum(all_priorities) / len(all_priorities) if all_priorities else 5
        
        summary = {
            'total_responses': len(valid_analyses),
            'top_pain_points': [item for item, count in pain_point_counts.most_common(5)],
            'common_behaviors': [item for item, count in behavior_counts.most_common(3)],
            'sentiment_breakdown': dict(sentiment_counts),
            'tech_comfort_levels': dict(tech_counts),
            'key_themes': [item for item, count in theme_counts.most_common(5)],
            'average_priority': round(avg_priority, 1),
            'priority_features': self._suggest_priority_features(pain_point_counts, behavior_counts, theme_counts),
            'key_risks': self._identify_risks(pain_point_counts, tech_counts),
            'market_opportunity': self._assess_opportunity(valid_analyses, avg_priority),
            'technology_readiness': self._assess_tech_readiness(tech_counts),
            'user_sentiment': self._assess_overall_sentiment(sentiment_counts),
            'next_actions': self._suggest_next_actions(pain_point_counts, sentiment_counts)
        }
        
        return summary
    
    def _suggest_priority_features(self, pain_points, behaviors, themes):
        """Suggest priority features based on analysis"""
        features = []
        
        top_pain_points = [p for p, c in pain_points.most_common(3)]
        top_themes = [t for t, c in themes.most_common(3)]
        
        if 'Stock Issues' in top_pain_points:
            features.append("Real-time inventory management system")
        
        if 'Insurance Delays' in top_pain_points or 'Insurance' in top_themes:
            features.append("Digital insurance claim processing")
        
        if 'Payment Issues' in top_pain_points or 'Cost' in top_themes:
            features.append("Multiple payment options (M-Pesa, cards, insurance)")
        
        if 'Technology Problems' in top_pain_points:
            features.append("Reliable, user-friendly mobile app")
        
        if 'Delivery Issues' in top_pain_points or 'Delivery' in top_themes:
            features.append("Efficient delivery and logistics system")
        
        # Add based on behaviors
        if behaviors.get('Mpesa Usage', 0) > 0:
            features.append("Enhanced M-Pesa integration")
        
        return features[:5]
    
    def _identify_risks(self, pain_points, tech_comfort):
        """Identify key risks"""
        risks = []
        
        if tech_comfort.get('Low', 0) > tech_comfort.get('High', 0):
            risks.append("Low technology adoption by some user segments")
        
        if pain_points.get('Stock Issues', 0) > 0:
            risks.append("Supply chain reliability and inventory management")
        
        if pain_points.get('Insurance Delays', 0) > 0:
            risks.append("Complex insurance integration requirements")
        
        risks.extend([
            "Regulatory compliance in healthcare sector",
            "Data security and privacy protection",
            "Competition from established pharmacy chains"
        ])
        
        return risks[:5]
    
    def _assess_opportunity(self, analyses, avg_priority):
        """Assess market opportunity"""
        total_responses = len(analyses)
        
        if total_responses < 3:
            return "Limited data available - collect more responses for comprehensive assessment"
        
        pain_point_count = sum(len(a.get('pain_points', [])) for a in analyses)
        avg_pain_points = pain_point_count / total_responses
        
        if avg_priority > 7 and avg_pain_points > 2:
            return "HIGH OPPORTUNITY: Significant pain points with high urgency across user segments"
        elif avg_priority > 6 or avg_pain_points > 1.5:
            return "MODERATE OPPORTUNITY: Clear pain points identified, good market potential"
        elif avg_pain_points > 1:
            return "EMERGING OPPORTUNITY: Some pain points identified, requires further validation"
        else:
            return "LIMITED OPPORTUNITY: Few pain points identified in current responses"
    
    def _assess_tech_readiness(self, tech_counts):
        """Assess overall technology readiness"""
        total = sum(tech_counts.values())
        if total == 0:
            return "Unable to assess - insufficient data"
        
        high_pct = (tech_counts.get('High', 0) / total) * 100
        low_pct = (tech_counts.get('Low', 0) / total) * 100
        
        if high_pct > 50:
            return f"HIGH READINESS: {high_pct:.0f}% show high technology comfort"
        elif high_pct > 30:
            return f"MODERATE READINESS: {high_pct:.0f}% high, {low_pct:.0f}% low technology comfort"
        else:
            return f"LOW READINESS: Only {high_pct:.0f}% show high technology comfort - focus on simple solutions"
    
    def _assess_overall_sentiment(self, sentiment_counts):
        """Assess overall user sentiment"""
        total = sum(sentiment_counts.values())
        if total == 0:
            return "Unable to assess sentiment"
        
        negative_pct = (sentiment_counts.get('Negative', 0) / total) * 100
        positive_pct = (sentiment_counts.get('Positive', 0) / total) * 100
        
        if negative_pct > 50:
            return f"CONCERNING: {negative_pct:.0f}% negative sentiment - major pain points exist"
        elif positive_pct > 50:
            return f"POSITIVE: {positive_pct:.0f}% positive sentiment - good market conditions"
        else:
            return f"MIXED: {negative_pct:.0f}% negative, {positive_pct:.0f}% positive - opportunities for improvement"
    
    def _suggest_next_actions(self, pain_points, sentiments):
        """Suggest immediate next actions"""
        actions = []
        
        top_pain_point = pain_points.most_common(1)
        if top_pain_point:
            actions.append(f"Address top pain point: {top_pain_point[0][0].lower()}")
        
        if sentiments.get('Negative', 0) > sentiments.get('Positive', 0):
            actions.append("Conduct deeper user interviews to understand frustrations")
        
        actions.extend([
            "Expand survey distribution to get more responses",
            "Validate findings with stakeholder interviews",
            "Develop minimum viable product (MVP) prototype"
        ])
        
        return actions[:3]

# Initialize analyzer
@st.cache_resource
def get_analyzer():
    return RuleBasedAnalyzer()

@st.cache_resource
def init_clients():
    try:
        # Check if running on Streamlit Cloud
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
            # Running locally
            credentials = Credentials.from_service_account_file(
                'credentials.json', 
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
        
        service = build('sheets', 'v4', credentials=credentials)
        return service
    except Exception as e:
        st.error(f"Setup error: {e}")
        return None

analyzer = get_analyzer()
service = init_clients()

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
        title="Responses by User Type",
        color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Rule-based analysis
    st.markdown("### 🧠 Rule-Based Analysis Results")
    
    # Analyze all responses
    all_analyses = []
    analysis_by_type = {}
    
    with st.spinner("Analyzing responses with rule-based system..."):
        for user_type in sheet_configs.keys():
            user_data = all_responses.get(user_type, {})
            if user_data.get('count', 0) > 0:
                type_analyses = []
                
                for response_row in user_data.get('responses', []):
                    analysis = analyzer.analyze_response_row(user_type, response_row)
                    if analysis:
                        type_analyses.append(analysis)
                        all_analyses.append(analysis)
                
                analysis_by_type[user_type] = type_analyses
    
    # Generate executive summary
    if all_analyses:
        executive_summary = analyzer.generate_summary(all_analyses)
        
        if executive_summary:
            st.markdown("### 🎯 Executive Summary")
            
            # Key metrics row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Responses Analyzed", executive_summary['total_responses'])
            with col2:
                st.metric("Avg Priority Score", f"{executive_summary['average_priority']}/10")
            with col3:
                sentiment_counts = executive_summary['sentiment_breakdown']
                dominant_sentiment = max(sentiment_counts.items(), key=lambda x: x[1])[0] if sentiment_counts else "Unknown"
                st.metric("Dominant Sentiment", dominant_sentiment)
            with col4:
                tech_counts = executive_summary['tech_comfort_levels']
                dominant_tech = max(tech_counts.items(), key=lambda x: x[1])[0] if tech_counts else "Unknown"
                st.metric("Tech Comfort Level", dominant_tech)
            
            # Detailed insights
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🚨 TOP PAIN POINTS:**")
                for pain_point in executive_summary['top_pain_points'][:5]:
                    st.write(f"• {pain_point}")
                
                st.markdown("**📱 TECHNOLOGY READINESS:**")
                st.write(executive_summary['technology_readiness'])
                
                st.markdown("**💰 MARKET OPPORTUNITY:**")
                st.write(executive_summary['market_opportunity'])
            
            with col2:
                st.markdown("**⭐ PRIORITY FEATURES:**")
                for feature in executive_summary['priority_features']:
                    st.write(f"• {feature}")
                
                st.markdown("**😊 USER SENTIMENT:**")
                st.write(executive_summary['user_sentiment'])
                
                st.markdown("**⚠️ KEY RISKS:**")
                for risk in executive_summary['key_risks'][:3]:
                    st.write(f"• {risk}")
            
            # Next actions
            st.markdown("**🎯 RECOMMENDED NEXT ACTIONS:**")
            action_cols = st.columns(len(executive_summary['next_actions']))
            
            for i, action in enumerate(executive_summary['next_actions']):
                with action_cols[i]:
                    if i == 0:
                        st.success(f"1. {action.title()}")
                    elif i == 1:
                        st.info(f"2. {action.title()}")
                    else:
                        st.warning(f"3. {action.title()}")
    
    st.markdown("---")
    
    # Detailed breakdown by user type
    st.markdown("### 🔍 Detailed Analysis by User Type")
    
    tabs = st.tabs(list(sheet_configs.keys()))
    
    for i, user_type in enumerate(sheet_configs.keys()):
        with tabs[i]:
            type_analyses = analysis_by_type.get(user_type, [])
            response_count = all_responses.get(user_type, {}).get('count', 0)
            
            if response_count > 0 and type_analyses:
                st.write(f"**{len(type_analyses)} {user_type} response(s) analyzed**")
                
                # User type specific metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**Pain Points:**")
                    type_pain_points = []
                    for analysis in type_analyses:
                        type_pain_points.extend(analysis.get('pain_points', []))
                    
                    if type_pain_points:
                        pain_counter = Counter(type_pain_points)
                        for pain, count in pain_counter.most_common(3):
                            st.write(f"• {pain} ({count})")
                    else:
                        st.write("No specific pain points identified")
                
                with col2:
                    st.write("**Behaviors:**")
                    type_behaviors = []
                    for analysis in type_analyses:
                        type_behaviors.extend(analysis.get('behaviors', []))
                    
                    if type_behaviors:
                        behavior_counter = Counter(type_behaviors)
                        for behavior, count in behavior_counter.most_common(3):
                            st.write(f"• {behavior} ({count})")
                    else:
                        st.write("No specific behaviors identified")
                
                with col3:
                    st.write("**Key Themes:**")
                    type_themes = []
                    for analysis in type_analyses:
                        type_themes.extend(analysis.get('key_themes', []))
                    
                    if type_themes:
                        theme_counter = Counter(type_themes)
                        for theme, count in theme_counter.most_common(3):
                            st.write(f"• {theme} ({count})")
                    else:
                        st.write("No major themes identified")
                
                # Sample insights
                st.write("**📝 Sample Response Insights:**")
                for j, analysis in enumerate(type_analyses[:2], 1):  # Show first 2
                    with st.expander(f"Response {j} - Priority: {analysis['priority_score']}/10"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Sentiment:** {analysis['sentiment']}")
                            st.write(f"**Tech Comfort:** {analysis['tech_comfort']}")
                            st.write(f"**Word Count:** {analysis['word_count']}")
                        with col2:
                            if analysis.get('sample_quote'):
                                st.write(f"**Key Quote:** *'{analysis['sample_quote']}'*")
            
            else:
                st.info(f"No {user_type.lower()} responses available yet.")
    
else:
    st.info("No responses collected yet. Share your survey links to start collecting data!")

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
st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ")