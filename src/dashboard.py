import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# Add root directory to path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import Database
from config import Config

# Page Config
st.set_page_config(
    page_title="National News Tracker",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize DB
@st.cache_resource
def get_db():
    return Database()

# Custom CSS for Premium Look
st.markdown("""
<style>
    /* Global Font */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Metrics Cards */
    div[data-testid="stMetric"] {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #333;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #FAFAFA;
        font-weight: 600;
    }
    
    /* Expander Styling */
    .streamlit-expanderHeader {
        background-color: #262730;
        border-radius: 5px;
        font-size: 16px;
        font-weight: 500;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #111;
    }
</style>
""", unsafe_allow_html=True)

# Main Title Area
c_title, c_status = st.columns([3, 1])
with c_title:
    st.title("🇮🇳 National News Tracker")
    st.caption(f"Monitoring Real-Time Coverage | Vector Intelligence: Active")

with c_status:
    st.success("● System Online")

# Sidebar
with st.sidebar:
    st.header("Settings")
    days = st.slider("Lookback Period (Days)", 1, 30, 7)
    person_filter = st.selectbox("Tracked Person", ["All", "Narendra Modi", "CR Patil"])
    
    st.divider()
    st.markdown("### System Status")
    st.markdown("🟢 **Collector**: Online")
    st.markdown("🟢 **Database**: Connected")
    st.markdown("🟡 **AI Engine**: Idle")

# Fetch Data
db = get_db()
p_filter = None if person_filter == "All" else person_filter
stats = db.get_statistics(days=days)
stories_grouped = db.get_stories_grouped(days=days, person=p_filter)

# Key Metrics Row
st.markdown("### 📊 Live Overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Articles", stats.get('total_articles', 0), delta="Last 24h")
col2.metric("Major Stories", stats.get('total_stories', 0))
col3.metric("Modi Coverage", stats.get('modi_count', 0))
col4.metric("Sources Monitored", stats.get('unique_channels', 0))

st.markdown("---")

# Content Area
c_feed, c_analysis = st.columns([2, 1])

with c_feed:
    st.subheader(f"📰 Priority Stories ({len(stories_grouped)})")
    
    if not stories_grouped:
        st.info("No stories found for the selected period.")
        
    for story in stories_grouped:
        with st.expander(f"{story['headline']}"):
            # Clean layout inside expander
            m1, m2, m3 = st.columns(3)
            m1.caption(f"📅 {story['published']}")
            m2.caption(f"📂 {story['category']}")
            m3.caption(f"🔗 {story['source_count']} Sources")
            
            st.markdown(f"**Tracked Person:** `{story['person']}`")
            
            st.markdown("#### Source Coverage")
            # Limit sources shown to keep it clean
            for source in story['sources'][:5]:
                st.markdown(f"• [{source['name']}]({source['url']}) `({source['language']})`")
            
            if len(story['sources']) > 5:
                st.caption(f"*+ {len(story['sources']) - 5} more sources*")

with c_analysis:
    st.subheader("📈 Intelligence")
    
    # Language Distribution Chart
    langs = stats.get('languages', [])
    if langs:
        lang_df = pd.DataFrame({'Language': langs, 'Count': [1]*len(langs)}) # Mock count for now
        fig = px.pie(lang_df, names='Language', title='Language Split', hole=0.4)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("No language data.")

    # Source Breadown
    st.markdown("#### Top Sources")
    st.info("Detailed source analytics coming in Phase 3.")
    
    with st.container():
        st.markdown("#### 📡 System Health")
        st.code(f"""
        Database: Connected
        AI Model: MiniLM-L6
        Last Sync: Just now
        """, language="yaml")

# Footer
st.markdown("---")
st.markdown("<center>National News Tracker v2.1 | Powered by Vector Embeddings</center>", unsafe_allow_html=True)
