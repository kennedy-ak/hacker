import streamlit as st
import sqlite3
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from bs4 import BeautifulSoup
import time
from dotenv import load_dotenv

load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Tech News Subscription",
    page_icon="📩",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Define color scheme
PRIMARY_COLOR = "#2e6db2"
SECONDARY_COLOR = "#f0f2f6" 
ACCENT_COLOR = "#FF5733"
TEXT_COLOR = "#333333"
CARD_BG_COLOR = "#1E293B"  # Dark blue-gray background instead of white
FORM_BG_COLOR = "#0F172A"  # Even darker background for forms

# Create database connection
def init_db():
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS subscribers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT
    )
    ''')
    conn.commit()
    return conn

# Get top Hacker News article
def get_top_article():
    try:
        response = requests.get("https://news.ycombinator.com/news")
        yc_page = response.text
        soup = BeautifulSoup(yc_page, 'html.parser')
        
        articles = soup.find_all(name='span', class_='titleline')
        article_scores = soup.find_all(name='span', class_='score')
        
        all_articles = [article.getText() for article in articles]
        all_links = [article.find('a').get("href") for article in articles]
        all_votes = [int(score.getText().split()[0]) for score in article_scores]

        highest_index = all_votes.index(max(all_votes))
        
        return all_articles[highest_index], all_links[highest_index]
    except Exception as e:
        st.error(f"Error fetching articles: {e}")
        return "Unable to fetch top article", "https://news.ycombinator.com"

# Send email function
def send_email(recipient, subject, message):
    try:
        # Email configuration
        sender_email = "kennedyakogokweku@gmail.com"
        password = os.getenv("password")  # App password
        
        # Create multipart message
        email_message = MIMEMultipart()
        email_message["From"] = sender_email
        email_message["To"] = recipient
        email_message["Subject"] = subject
        
        # Add body to email
        email_message.attach(MIMEText(message, "plain"))
        
        # Connect to server and send
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.send_message(email_message)
        
        return True
    except Exception as e:
        st.error(f"Error sending email: {e}")
        return False

# Function to send daily news to all subscribers
def send_daily_news():
    conn = init_db()
    c = conn.cursor()
    c.execute("SELECT name, email FROM subscribers")
    subscribers = c.fetchall()
    
    article_title, article_link = get_top_article()
    subject = "Top Tech News Article"
    
    success_count = 0
    total_count = len(subscribers)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, (name, email) in enumerate(subscribers):
        personalized_message = f"Hi {name},\n\nToday's Top Tech article: {article_title}\nRead more at: {article_link}\n\nCheers,\n Kennedy Akogo"
        
        if send_email(email, subject, personalized_message):
            success_count += 1
        
        # Update progress
        progress = (i + 1) / total_count
        progress_bar.progress(progress)
        status_text.text(f"Sending emails: {i+1}/{total_count}")
        time.sleep(0.1)  # Small delay to avoid hitting rate limits
    
    status_text.text(f"Completed! Successfully sent {success_count} out of {total_count} emails.")
    return success_count, total_count

# Function to add new subscriber
def add_subscriber(name, email, phone):
    conn = init_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO subscribers (name, email, phone) VALUES (?, ?, ?)", 
                 (name, email, phone))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        st.error("This email address is already subscribed.")
        return False
    finally:
        conn.close()

# Main app
def main():
    # Check for admin password in session state
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False
    
    # Header with gradient background
    st.markdown('<div class="header-container"><h1>Tech News Service</h1></div>', unsafe_allow_html=True)
    
    # Create tabs for user and admin interfaces with custom styling
    tab1, tab2 = st.tabs(["📮 Subscribe", "🔐 Admin"])
    
    # User subscription form
    with tab1:
        st.markdown('<div class="tech-card">', unsafe_allow_html=True)
        st.markdown('### 📱 Get Daily Tech News Updates')
        st.write("Subscribe to receive the top tech news article in your inbox every day. Stay informed about the latest innovations and developments in the tech world!")
        
        # Add system explanation
        st.markdown("""
        <div style="margin-top: 15px; padding: 15px; background-color: #172554; border-radius: 8px; border: 1px solid #1E40AF;">
            <h4 style="color: #60A5FA;">How the System Works</h4>
            <p style="color: #CBD5E1; font-size: 0.9rem;">
                <strong>📰 News Source:</strong> We  the most popular and relevant articles from <a href="https://news.ycombinator.com" style="color: #93C5FD;">Hacker News</a>, a trusted community-driven platform for tech enthusiasts.
            </p>
            <p style="color: #CBD5E1; font-size: 0.9rem;">
                <strong>🔍 Selection Process:</strong> Our algorithm automatically selects the highest-voted article of the day, ensuring you only receive content that the tech community finds valuable and interesting.
            </p>
            <p style="color: #CBD5E1; font-size: 0.9rem;">
                <strong>⏰ Delivery:</strong> Each newsletter is delivered directly to your inbox daily, keeping you consistently updated without overwhelming you with too much content.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Featured article preview (optional)
        with st.expander("📰 See today's featured article"):
            try:
                title, link = get_top_article()
                st.markdown(f"### {title}")
                st.markdown(f"[Read the full article]({link})")
            except:
                st.write("Preview not available. Subscribe to receive articles by email!")
        
        st.markdown('<div class="form-container">', unsafe_allow_html=True)
        with st.form("subscription_form"):
            st.markdown("### Join the News-Letter ")
            name = st.text_input("Full Name", placeholder="Enter your name")
            email = st.text_input("Email Address", placeholder="your.email@example.com")
            phone = st.text_input("Phone Number", placeholder="Optional")
            
            # Add terms checkbox
            terms_agree = st.checkbox("I agree to receive daily tech news updates")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submitted = st.form_submit_button("🚀 Subscribe Now")
            
            if submitted:
                if not name or not email:
                    st.error("Please fill in all required fields.")
                elif "@" not in email:
                    st.error("Please enter a valid email address.")
                elif not terms_agree:
                    st.error("Please agree to receive the newsletter to subscribe.")
                else:
                    if add_subscriber(name, email, phone):
                        st.markdown('<div class="success-message">', unsafe_allow_html=True)
                        st.success("🎉 You have successfully subscribed!")
                        st.markdown("</div>", unsafe_allow_html=True)
                        st.balloons()
                        
                        # Create success card with more info
                        st.markdown("""
                        <div style="background-color: #172554; padding: 20px; border-radius: 10px; text-align: center; margin-top: 20px; border: 1px solid #1E40AF;">
                            <h3 style="color: white;">Welcome to our Tech Community!</h3>
                            <p style="color: #CBD5E1;">Your first newsletter will arrive shortly. Meanwhile, check out our featured article for today!</p>
                            <p style="font-size: 0.8rem; color: #94A3B8;">You can unsubscribe at any time by clicking the link in the email.</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Send a welcome email
                        welcome_subject = "Welcome to Tech News Subscription!"
                        welcome_message = f"""Hi {name},

Thank you for subscribing to my Tech News service! 🎉

You'll now receive daily updates on the lastest tech trends directly in your inbox. I have curated the most interesting and impactful stories from around the tech world to keep you informed.

Today's Top Article:
{get_top_article()[0]}

I am excited to have you join my tech community!


Cheers,
Kennedy - AI/LLM engineer.
"""
                        send_email(email, welcome_subject, welcome_message)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Add testimonials section
        # st.markdown("""
        # <div style="margin-top: 30px; padding: 20px; background-color: #1E293B; border-radius: 10px; border: 1px solid #334155;">
        #     <h3 style="text-align: center; color: white;">What Our Subscribers Say</h3>
        #     <div style="display: flex; justify-content: space-between; flex-wrap: wrap;">
        #         <div style="flex: 1; min-width: 200px; padding: 15px;">
        #             <p style="font-style: italic; color: #CBD5E1;">"This daily newsletter keeps me updated on all the latest tech trends without having to browse multiple sites!"</p>
        #             <p style="text-align: right; font-weight: bold; color: #60A5FA;">- Sarah K.</p>
        #         </div>
        #         <div style="flex: 1; min-width: 200px; padding: 15px;">
        #             <p style="font-style: italic; color: #CBD5E1;">"The curated content is excellent. I always find something interesting to read during my morning coffee."</p>
        #             <p style="text-align: right; font-weight: bold; color: #60A5FA;">- Michael T.</p>
        #         </div>
        #     </div>
        # </div>
        # """, unsafe_allow_html=True)
    
    # Admin interface
    with tab2:
        st.markdown('<div class="tech-card">', unsafe_allow_html=True)
        st.markdown("### 🔐 Admin Dashboard")
        st.markdown("Access the administrative functions to manage subscribers and send newsletters.")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if not st.session_state.is_admin:
            st.markdown('<div class="form-container">', unsafe_allow_html=True)
            with st.form("admin_login"):
                st.markdown("### Admin Login")
                password = st.text_input("Admin Password", type="password", placeholder="Enter admin password")
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    login_submitted = st.form_submit_button("🔑 Login")
                
                if login_submitted:
                    # Simple password check - in production, use a more secure method
                    if password == os.getenv("ADMIN_PASSWORD"):
                        st.session_state.is_admin = True
                        st.rerun()
                    else:
                        st.error("Incorrect password")
            st.markdown('</div>', unsafe_allow_html=True)
        
        else:
            st.success("✅ Admin logged in successfully")
            
            # Create dashboard metrics
            conn = init_db()
            df = pd.read_sql_query("SELECT * FROM subscribers", conn)
            conn.close()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                subscriber_count = len(df)
                st.markdown(f"""
                <div style="background-color: #172554; padding: 20px; border-radius: 10px; text-align: center; height: 150px; border: 1px solid #1E40AF;">
                    <h4 style="color: #60A5FA;">Total Subscribers</h4>
                    <h2 style="font-size: 3rem; margin: 10px 10px; color: white;">{subscriber_count}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                today = pd.Timestamp.now().strftime('%Y-%m-%d')
                # Improved method to count new subscribers today
                new_today = len(df[df['id'] == df['id'].max()]) if not df.empty else 0
                st.markdown(f"""
                <div style="background-color: #172554; padding: 20px; border-radius: 10px; text-align: center; height: 150px; border: 1px solid #1E40AF;">
                    <h4 style="color: #60A5FA;">New Today</h4>
                    <h2 style="font-size: 3rem; margin: 10px 0; color: white;">{new_today}</h2>
                </div>
                """, unsafe_allow_html=True)
            # with col1:
            #     st.markdown("""
            #     <div style="background-color: #172554; padding: 20px; border-radius: 10px; text-align: center; height: 150px; border: 1px solid #1E40AF;">
            #         <h4 style="color: #60A5FA;">Total Subscribers</h4>
            #         <h2 style="font-size: 3rem; margin: 10px 10px; color: white;">{}</h2>
            #     </div>
            #     """.format(len(df)), unsafe_allow_html=True)
            
            # with col2:
            #     today = pd.Timestamp.now().strftime('%Y-%m-%d')
            #     new_today = len(df[df['id'] == df['id'].max()]) if not df.empty else 0
            #     st.markdown("""
            #     <div style="background-color: #172554; padding: 20px; border-radius: 10px; text-align: center; height: 150px; border: 1px solid #1E40AF;">
            #         <h4 style="color: #60A5FA;">New Today</h4>
            #         <h2 style="font-size: 3rem; margin: 10px 0; color: white;">{}</h2>
            #     </div>
            #     """.format(new_today), unsafe_allow_html=True)
            
            with col3:
                st.markdown("""
                <div style="background-color: #172554; padding: 20px; border-radius: 10px; text-align: center; height: 150px; border: 1px solid #1E40AF;">
                    <h4 style="color: #60A5FA;">Newsletter Status</h4>
                    <h2 style="font-size: 1.5rem; margin: 10px 0; color: #FBBF24;">Ready to Send</h2>
                </div>
                """, unsafe_allow_html=True)
            
            # Newsletter control panel
            st.markdown("""
            <div style="background-color: #1E3A8A; padding: 25px; border-radius: 10px; margin: 20px 0; border: 1px solid #2563EB;">
                <h3 style="color: white; text-align: center;">Newsletter Control Panel</h3>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Preview today's newsletter
                st.markdown('<div style="background-color: #172554; padding: 20px; border-radius: 10px; height: 100%; border: 1px solid #1E40AF;">', unsafe_allow_html=True)
                st.markdown("### 📰 Today's Newsletter")
                try:
                    title, link = get_top_article()
                    st.markdown(f"**Title:** {title}")
                    st.markdown(f"**Link:** [Read the full article]({link})")
                    st.markdown("**Preview:**")
                    st.info(f"Today's Top Tech article: {title}\nRead more at: {link}")
                except:
                    st.error("Unable to fetch today's article. Please try again later.")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                # Newsletter controls
                st.markdown('<div style="background-color: #172554; padding: 20px; border-radius: 10px; height: 100%; border: 1px solid #1E40AF;">', unsafe_allow_html=True)
                st.markdown("### 📤 Send Newsletter")
                st.write("Send the daily newsletter to all subscribers with one click.")
                
                if st.button("📧 Send to All Subscribers", use_container_width=True):
                    with st.spinner("Preparing to send newsletters..."):
                        # Add a more detailed progress display
                        progress_container = st.empty()
                        progress_container.markdown("""
                        <div style="background-color: #075985; padding: 20px; border-radius: 10px; text-align: center;">
                            <h4 style="color: white;">Preparing newsletter...</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        success_count, total_count = send_daily_news()
                        
                    if success_count > 0:
                        progress_container.markdown(f"""
                        <div style="background-color: #065F46; padding: 20px; border-radius: 10px; text-align: center;">
                            <h4 style="color: white;">✅ Successfully sent {success_count} out of {total_count} emails!</h4>
                            <p style="color: #A7F3D0;">The newsletter has been delivered to your subscribers.</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        progress_container.markdown("""
                        <div style="background-color: #7F1D1D; padding: 20px; border-radius: 10px; text-align: center;">
                            <h4 style="color: white;">❌ Failed to send emails</h4>
                            <p style="color: #FECACA;">Please check your email configuration and try again.</p>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Test email option
                st.markdown("### 🧪 Test Newsletter")
                test_email = st.text_input("Send test to email", placeholder="your.email@example.com")
                if st.button("📤 Send Test Email", use_container_width=True) and test_email:
                    if "@" in test_email:
                        with st.spinner("Sending test email..."):
                            title, link = get_top_article()
                            subject = "Tech News Newsletter - TEST"
                            message = f"""Hi there,

This is a TEST email of our Tech News newsletter.

Today's Top Tech article: {title}
Read more at: {link}

Thanks for being a subscriber!
Tech News Team
"""
                            if send_email(test_email, subject, message):
                                st.success("✅ Test email sent successfully!")
                            else:
                                st.error("❌ Failed to send test email.")
                    else:
                        st.error("Please enter a valid email address for testing.")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Subscriber management
            st.markdown("""
            <div style="background-color: #1E3A8A; padding: 25px; border-radius: 10px; margin: 20px 0; border: 1px solid #2563EB;">
                <h3 style="color: white; text-align: center;">Subscriber Management</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Display subscribers in a nicer table
            st.markdown("### 👥 Current Subscribers")
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    # Export options
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Export as CSV",
                        data=csv,
                        file_name="subscribers.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col2:
                    # Logout button styled
                    if st.button("🚪 Logout", use_container_width=True):
                        st.session_state.is_admin = False
                        st.rerun()
            else:
                st.info("No subscribers yet. Share your subscription form to get started!")
                
                # Logout button when no subscribers
                if st.button("🚪 Logout", use_container_width=True):
                    st.session_state.is_admin = False
                    st.rerun()

# Custom CSS to improve the appearance
st.markdown(f"""
<style>
    .stApp {{
        background-color: #0F172A; /* Dark background for entire app */
    }}
    .stTabs [data-baseweb="tab"] {{
        font-size: 20px;
        font-weight: bold;
        color: white;
    }}
    h1, h2, h3 {{
        color: white;
        font-family: 'Segoe UI', 'Roboto', sans-serif;
    }}
    .stTabs [aria-selected="true"] {{
        color: #64B5F6 !important;
        border-bottom-color: #64B5F6 !important;
    }}
    h1 {{
        font-size: 2.5rem;
        margin-bottom: 1.5rem;
        text-align: center;
    }}
    .stButton>button {{
        background-color: #3B82F6;
        color: white;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: bold;
        transition: all 0.3s ease;
        width: 100%;
        margin-top: 10px;
    }}
    .stButton>button:hover {{
        background-color: #2563EB;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
    }}
    .success-message {{
        padding: 20px;
        background-color: #064E3B;
        color: white;
        border-radius: 8px;
        margin-bottom: 20px;
    }}
    .stTextInput>div>div>input, .stNumberInput>div>div>input {{
        border-radius: 8px;
        border: 1px solid #334155;
        padding: 12px 15px;
        background-color: #1E293B;
        color: white;
    }}
    .stTextInput>label, .stNumberInput>label, .stCheckbox>label {{
        color: #E2E8F0 !important;
    }}
    p {{
        color: #CBD5E1;
    }}
    .tech-card {{
        background-color: {CARD_BG_COLOR};
        border-radius: 12px;
        padding: 25px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        margin-bottom: 20px;
        color: #E2E8F0;
        border: 1px solid #334155;
    }}
    .header-container {{
        background-image: linear-gradient(135deg, #1E40AF, #1E3A8A);
        padding: 30px 0;
        border-radius: 12px;
        margin-bottom: 30px;
        text-align: center;
        color: white;
    }}
    .tech-icon {{
        font-size: 24px;
        margin-right: 10px;
    }}
    .form-container {{
        background-color: {FORM_BG_COLOR};
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        border: 1px solid #334155;
    }}
    .stDataFrame {{
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        background-color: {CARD_BG_COLOR};
    }}
    .stDataFrame th {{
        background-color: #334155 !important;
        color: white !important;
    }}
    .stDataFrame td {{
        color: #E2E8F0 !important;
    }}
    .floating-icons {{
        position: absolute;
        width: 100%;
        height: 100%;
        top: 0;
        left: 0;
        overflow: hidden;
        pointer-events: none;
        z-index: -1;
    }}
    .tech-float {{
        position: absolute;
        opacity: 0.08;
        font-size: 2rem;
        animation: float 15s infinite ease-in-out;
    }}
    @keyframes float {{
        0%, 100% {{ transform: translateY(0) rotate(0deg); }}
        50% {{ transform: translateY(100px) rotate(10deg); }}
    }}
    .stExpander {{
        background-color: {CARD_BG_COLOR} !important;
        border-radius: 8px !important;
        border: 1px solid #334155 !important;
    }}
    .stExpander > details > summary {{
        color: #E2E8F0 !important;
    }}
    .stExpander > details > div {{
        background-color: {CARD_BG_COLOR} !important;
    }}
    .stAlert {{
        background-color: #172554 !important;
        color: #E2E8F0 !important;
    }}
    .stSpinner > div {{
        border-top-color: #3B82F6 !important;
    }}
</style>
""", unsafe_allow_html=True)

# Add floating tech icons in background
def add_floating_icons():
    icons = "🔧 💻 📱 🌐 🔍 📊 🚀 🔒 🌟 📡"
    html = '<div class="floating-icons">'
    
    for i in range(15):
        icon = icons[i % len(icons)]
        left = i * 7
        delay = i * 0.5
        top = (i * 13) % 90
        html += f'<div class="tech-float" style="left:{left}%; top:{top}%; animation-delay:{delay}s;">{icon}</div>'
    
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

add_floating_icons()

if __name__ == "__main__":
    main()
