"""
Streamlit UI for MCP Bilingual Terminology Checker
"""
import streamlit as st
import requests
import json
import os
from typing import List, Dict

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "TEST_TOKEN")

st.set_page_config(
    page_title="Bilingual MCP Terminology Checker",
    page_icon="🔍",
    layout="wide"
)

def call_api(text: str, language: str, context: str = "", use_llm: bool = False) -> Dict:
    """Call the MCP API to check terminology."""
    url = f"{API_BASE_URL}/context-request"
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "lang": language,
        "context": context
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None

def display_issues(issues: List[Dict], original_text: str):
    """Display terminology issues in a formatted table."""
    if not issues:
        st.success("✅ No terminology issues found!")
        return
    
    st.warning(f"⚠️ Found {len(issues)} terminology issue(s)")
    
    # Create a table of issues
    for i, issue in enumerate(issues, 1):
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 3])
            
            with col1:
                severity_color = {
                    "error": "🔴",
                    "warning": "🟡", 
                    "info": "🔵"
                }.get(issue.get("severity", "warning"), "🟡")
                st.write(f"{severity_color} **Issue #{i}**")
            
            with col2:
                st.write(f"**Original:** `{issue['original']}`")
                st.write(f"**Suggestion:** `{issue['suggestion']}`")
            
            with col3:
                st.write(f"**Type:** {issue['type']}")
                st.write(f"**Reason:** {issue.get('reason', 'Terminology improvement')}")
            
            st.divider()

def main():
    st.title("🔍 Bilingual MCP Terminology Checker")
    st.markdown("**Professional EN ↔ JP UI terminology validation with AI assistance**")
    
    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # API status check
        try:
            health_response = requests.get(f"{API_BASE_URL}/health", timeout=10)
            if health_response.status_code == 200:
                st.success("✅ API Connected")
                health_data = health_response.json()
                llm_status = "🤖 LLM Available" if health_data.get("llm_available") else "📚 Database Only"
                st.info(llm_status)
            else:
                st.error("❌ API Unavailable")
        except:
            st.error("❌ Cannot reach API")
        
        st.markdown("---")
        st.markdown("**About this demo:**")
        st.markdown("• 189k+ professional terminology entries")
        st.markdown("• Microsoft Japanese standards")
        st.markdown("• Real-time terminology checking")
        st.markdown("• MCP protocol compatible")
    
    # Main interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        text_input = st.text_area(
            "Enter text to check:",
            height=120,
            placeholder="e.g., Please login to access your e-mail account",
            help="Enter English or Japanese UI text for terminology analysis"
        )
    
    with col2:
        language = st.selectbox(
            "Language:",
            options=["en", "jp"],
            format_func=lambda x: "🇺🇸 English" if x == "en" else "🇯🇵 Japanese",
            help="Select the language of your input text"
        )
        
        context = st.text_input(
            "Context (optional):",
            placeholder="e.g., login button, error message",
            help="Describe where this text appears for better suggestions"
        )
        
        use_llm = st.checkbox(
            "🤖 Use AI analysis",
            value=False,
            help="Enable LLM-powered suggestions (may consume tokens)"
        )
    
    # Analysis button
    if st.button("🔍 Analyze Terminology", type="primary", use_container_width=True):
        if not text_input.strip():
            st.warning("Please enter some text to analyze.")
            return
        
        with st.spinner("Analyzing terminology..."):
            result = call_api(text_input, language, context, use_llm)
        
        if result:
            # Display results
            st.markdown("---")
            st.subheader("📋 Analysis Results")
            
            # Show analysis metadata
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Language", "🇺🇸 English" if language == "en" else "🇯🇵 Japanese")
            with col2:
                st.metric("Issues Found", len(result.get("issues", [])))
            with col3:
                llm_used = result.get("llm_used", False)
                st.metric("Analysis Type", "🤖 AI + DB" if llm_used else "📚 Database")
            
            # Display issues
            issues = result.get("issues", [])
            display_issues(issues, text_input)
            
            # Show original text for reference
            with st.expander("📝 Original Text"):
                st.code(text_input, language=language)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "Built with FastAPI + MCP Protocol • "
        "Database: 189k+ professional terms • "
        "[GitHub Repository](https://github.com/wy-yang-lab/Bilingual_MCP)"
    )

if __name__ == "__main__":
    main() 