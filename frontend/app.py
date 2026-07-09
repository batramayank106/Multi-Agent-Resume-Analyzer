import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import base64
import streamlit as st

ICON_PATH = Path(__file__).parent.parent / "media and images" / "Main icon transparent.png"

def img_to_base64(path):
    return base64.b64encode(Path(path).read_bytes()).decode()

icon_b64 = img_to_base64(ICON_PATH)

st.set_page_config(
    page_title="CV Chacha — by Mayank Batra",
    page_icon=str(ICON_PATH),
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');



    :root {
        --canvas: #faf9f5;
        --ink: #141413;
        --body: #3d3d3a;
        --body-strong: #252523;
        --muted: #6c6a64;
        --muted-soft: #8e8b82;
        --hairline: #e6dfd8;
        --surface-card: #efe9de;
        --surface-soft: #f5f0e8;
        --surface-dark: #181715;
        --surface-dark-elevated: #252320;
        --primary: #cc785c;
        --primary-active: #a9583e;
        --on-primary: #ffffff;
        --on-dark: #faf9f5;
        --on-dark-soft: #a09d96;
        --accent-teal: #5db8a6;
        --success: #5db872;
        --warning: #d4a017;
        --error: #c64545;
    }

    .stApp { background: var(--canvas); }
    .main > div { background: transparent; }

    section[data-testid="stSidebar"] {
        background: var(--surface-dark) !important;
        border-right: 1px solid var(--surface-dark-elevated);
    }
    section[data-testid="stSidebar"] * { color: var(--on-dark-soft) !important; }
    section[data-testid="stSidebar"] hr { border-color: #252320 !important; }
    section[data-testid="stSidebar"] .stPageLink {
        padding: 5px 12px !important;
        border-radius: 6px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 13px !important;
        color: #a09d96 !important;
        text-decoration: none !important;
        display: block !important;
        margin: 1px 0 !important;
    }
    section[data-testid="stSidebar"] .stPageLink:hover {
        background: rgba(204, 120, 92, 0.08) !important;
        color: #faf9f5 !important;
    }
    section[data-testid="stSidebar"] .stPageLink[aria-current="page"] {
        background: rgba(204, 120, 92, 0.15) !important;
        color: #faf9f5 !important;
        font-weight: 500 !important;
        border: 1px solid rgba(204, 120, 92, 0.25) !important;
    }

    h1, h2, h3 {
        font-family: 'Playfair Display', 'Georgia', serif !important;
        color: var(--ink) !important;
        font-weight: 400 !important;
        letter-spacing: -0.5px !important;
    }
    h1 { font-size: 2.8rem !important; line-height: 1.1 !important; }
    h2 { font-size: 2rem !important; line-height: 1.15 !important; }
    h3 { font-size: 1.4rem !important; line-height: 1.2 !important; }
    p, li, .stMarkdown, .stText {
        font-family: 'Inter', system-ui, sans-serif !important;
        color: var(--body) !important;
        font-size: 15px !important;
        line-height: 1.6 !important;
    }
    .stButton > button {
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        background: var(--primary) !important;
        color: var(--on-primary) !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 20px !important;
        height: 40px !important;
    }
    .stButton > button:hover { background: var(--primary-active) !important; }
    div[data-testid="stMetricValue"] {
        color: var(--ink) !important;
        font-family: 'Playfair Display', serif !important;
        font-size: 2rem !important;
        font-weight: 400 !important;
    }
    div[data-testid="stMetricLabel"] {
        color: var(--muted) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1.5px !important;
        font-weight: 500 !important;
    }
    .stAlert { background: var(--surface-soft) !important; border: 1px solid var(--hairline) !important; color: var(--body) !important; border-radius: 8px !important; }
    .stInfo { background: var(--surface-soft) !important; border: 1px solid var(--hairline) !important; color: var(--body) !important; }
    .stSuccess { background: rgba(93, 184, 114, 0.1) !important; border: 1px solid var(--success) !important; color: var(--body) !important; }
    .stWarning { background: rgba(212, 160, 23, 0.1) !important; border: 1px solid var(--warning) !important; color: var(--body) !important; }
    .stError { background: rgba(198, 69, 69, 0.1) !important; border: 1px solid var(--error) !important; color: var(--body) !important; }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--surface-soft); }
    ::-webkit-scrollbar-thumb { background: var(--muted-soft); border-radius: 3px; }
    hr { border-color: var(--hairline) !important; }
    div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {
        background: var(--surface-soft) !important;
        border: 1px solid var(--hairline) !important;
        border-radius: 6px !important;
        color: var(--ink) !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 2px !important; border-bottom: 1px solid var(--hairline) !important; }
    .stTabs [data-baseweb="tab"] { color: var(--muted) !important; font-family: 'Inter', sans-serif !important; font-weight: 500 !important; font-size: 14px !important; padding: 8px 20px !important; }
    .stTabs [aria-selected="true"] { color: var(--ink) !important; border-bottom: 2px solid var(--primary) !important; }
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] { gap: 0.3rem !important; }
    div.stRadio > div[role="radiogroup"] { gap: 0 !important; }
    div.stRadio > div[role="radiogroup"] label {
        padding: 6px 16px !important; margin-right: 0 !important; border-radius: 0 !important;
        border: 1px solid var(--hairline) !important; border-right: none !important;
        background: var(--surface-soft) !important; font-size: 0.85rem !important;
    }
    div.stRadio > div[role="radiogroup"] label:first-child { border-radius: 6px 0 0 6px !important; }
    div.stRadio > div[role="radiogroup"] label:last-child { border-radius: 0 6px 6px 0 !important; border-right: 1px solid var(--hairline) !important; }
    div.stRadio > div[role="radiogroup"] label[data-checked="true"] { background: var(--primary) !important; color: var(--on-primary) !important; border-color: var(--primary) !important; }

    .cv-loader-wrap {
        display: flex; justify-content: center; align-items: center;
        min-height: 50vh; flex-direction: column; gap: 1rem;
    }
    .cv-loader { display: flex; gap: 10px; }
    .cv-dot {
        width: 14px; height: 14px; border-radius: 50%;
        background: var(--primary);
        animation: cv-bounce 1.4s ease-in-out infinite both;
    }
    .cv-dot:nth-child(1) { animation-delay: -0.32s; }
    .cv-dot:nth-child(2) { animation-delay: -0.16s; }
    .cv-dot:nth-child(3) { animation-delay: 0s; }
    @keyframes cv-bounce {
        0%, 80%, 100% { transform: scale(0); opacity: 0.4; }
        40% { transform: scale(1); opacity: 1; }
    }
    .cv-loader-text {
        color: var(--muted); font-family: 'Inter', sans-serif;
        font-size: 0.85rem; letter-spacing: 1px;
        text-transform: uppercase; animation: cv-pulse-text 1.5s ease-in-out infinite;
    }
    @keyframes cv-pulse-text {
        0%, 100% { opacity: 0.5; }
        50% { opacity: 1; }
    }

    .ats-loader-wrap {
        display: flex; justify-content: center; align-items: center;
        min-height: 50vh; flex-direction: column; gap: 0.5rem;
    }
    .ats-gauge {
        position: relative; width: 120px; height: 60px;
        background: linear-gradient(90deg, var(--error) 0%, var(--warning) 50%, var(--success) 100%);
        border-radius: 60px 60px 0 0; overflow: hidden;
        animation: ats-pulse 0.6s ease-in-out infinite alternate;
    }
    .ats-needle {
        position: absolute; bottom: 0; left: 50%;
        width: 3px; height: 55px; background: var(--ink);
        transform-origin: bottom center;
        animation: ats-sweep 1.8s ease-in-out infinite;
    }
    @keyframes ats-sweep {
        0% { transform: translateX(-50%) rotate(-45deg); }
        50% { transform: translateX(-50%) rotate(45deg); }
        100% { transform: translateX(-50%) rotate(-45deg); }
    }
    @keyframes ats-pulse {
        from { box-shadow: 0 0 10px rgba(204, 120, 92, 0.3); }
        to { box-shadow: 0 0 25px rgba(204, 120, 92, 0.6); }
    }
    .ats-score-rings {
        position: absolute; bottom: -5px; left: 0; right: 0;
        display: flex; justify-content: space-between; padding: 0 5px;
        font-size: 0.6rem; color: var(--muted);
    }
    .ats-loader-text {
        color: var(--muted); font-family: 'Inter', sans-serif;
        font-size: 0.8rem; letter-spacing: 1px;
    }

    .pl-wrap {
        display: flex; justify-content: center; align-items: center;
        min-height: 40vh; flex-direction: column; gap: 1.5rem;
    }
    .pl-title {
        color: var(--muted); font-family: 'Inter', sans-serif;
        font-size: 0.85rem; letter-spacing: 2px; text-transform: uppercase;
    }
    .pl-flow {
        display: flex; align-items: center; flex-wrap: wrap;
        justify-content: center; gap: 0.5rem;
    }
    .pl-node {
        display: flex; flex-direction: column; align-items: center; gap: 4px;
        padding: 0.5rem; border-radius: 8px; min-width: 70px;
    }
    .pl-node .pl-check {
        width: 24px; height: 24px; border-radius: 50%;
        background: var(--success); color: white;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.7rem; font-weight: 700;
    }
    .pl-node .pl-pulse {
        width: 24px; height: 24px; border-radius: 50%;
        background: var(--primary);
        animation: cv-bounce 0.8s ease-in-out infinite;
    }
    .pl-node .pl-dot {
        width: 24px; height: 24px; border-radius: 50%;
        background: var(--hairline); opacity: 0.6;
    }
    .pl-node span {
        font-family: 'Inter', sans-serif; font-size: 0.65rem;
        color: var(--muted); text-align: center; white-space: nowrap;
    }
    .pl-node.done span { color: var(--success); }
    .pl-node.active span { color: var(--primary); font-weight: 500; }
    .pl-arrow {
        width: 20px; height: 2px; background: var(--hairline);
        position: relative;
    }
    .pl-arrow::after {
        content: '›'; position: absolute; right: -4px; top: 50%;
        transform: translateY(-50%); color: var(--hairline);
        font-size: 1rem; line-height: 1;
    }
    .pl-arrow.active { background: var(--primary); }
    .pl-arrow.active::after { color: var(--primary); }

    .pl-status-badges {
        display: flex; flex-wrap: wrap; gap: 0.4rem; justify-content: center; margin-top: 0.5rem;
    }
    .pl-status-badge {
        display: inline-flex; align-items: center; gap: 4px;
        padding: 3px 10px; border-radius: 12px; font-size: 0.7rem;
        font-family: 'Inter', sans-serif; font-weight: 500;
    }
    .pl-status-badge.done {
        background: rgba(93, 184, 114, 0.15); color: var(--success); border: 1px solid rgba(93, 184, 114, 0.3);
    }
    .pl-status-badge.running {
        background: rgba(204, 120, 92, 0.15); color: var(--primary); border: 1px solid rgba(204, 120, 92, 0.3);
        animation: cv-pulse-text 1.2s ease-in-out infinite;
    }
    .pl-status-badge.pending {
        background: var(--surface-soft); color: var(--muted-soft); border: 1px solid var(--hairline);
    }

    /* ── Liquid Glass Card ── */
    .liquid-glass {
        backdrop-filter: blur(4px);
        background: rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 2.5rem 2rem;
        position: relative;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1),
                    0 8px 32px rgba(0, 0, 0, 0.3);
    }
    .liquid-glass::before {
        content: '';
        position: absolute;
        inset: 0;
        border-radius: 16px;
        padding: 1px;
        background: linear-gradient(135deg, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0.05) 50%, rgba(255,255,255,0) 100%);
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor;
        mask-composite: exclude;
        pointer-events: none;
    }
    .liquid-glass input, .liquid-glass textarea {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        color: #fff !important;
        border-radius: 8px !important;
    }
    .liquid-glass input::placeholder, .liquid-glass textarea::placeholder {
        color: rgba(255,255,255,0.4) !important;
    }

    /* ── Login Page ── */
    .login-tab-btn {
        background: transparent !important;
        color: rgba(255,255,255,0.5) !important;
        border: none !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 14px !important;
        padding: 8px 24px !important;
        border-radius: 0 !important;
        border-bottom: 2px solid transparent !important;
        transition: all 0.2s !important;
    }
    .login-tab-btn:hover {
        color: rgba(255,255,255,0.8) !important;
        background: transparent !important;
    }
    .login-tab-btn[aria-selected="true"] {
        color: #fff !important;
        background: transparent !important;
        border-bottom: 2px solid var(--primary) !important;
    }

</style>
""", unsafe_allow_html=True)

from frontend.utils.state import init as init_state, is_authenticated, is_super_admin
init_state()

_page_cache = {}
def _lazy(mod_name):
    def render():
        if mod_name not in _page_cache:
            import importlib
            _page_cache[mod_name] = importlib.import_module(f"frontend.pages.{mod_name}")
        return _page_cache[mod_name].render()
    render.__module__ = f"frontend.pages.{mod_name}"
    render.__name__ = "render"
    return render

pages = [
    st.Page(_lazy("login"), title="Login / Sign Up", icon="🔐", url_path="login"),
    st.Page(_lazy("dashboard"), title="Dashboard", icon="🏠", url_path="dashboard"),
    st.Page(_lazy("vault"), title="Resume Vault", icon="📂", url_path="vault"),
    st.Page(_lazy("resume_library"), title="Resume Library", icon="📚", url_path="resume_library"),
    st.Page(_lazy("resume_upload"), title="Upload Resume", icon="📄", url_path="resume_upload"),
    st.Page(_lazy("jd_upload"), title="Upload JD", icon="📋", url_path="jd_upload"),
    st.Page(_lazy("ats_analysis"), title="ATS Analysis", icon="✅", url_path="ats"),
    st.Page(_lazy("recruiter_review"), title="Recruiter Review", icon="👔", url_path="recruiter"),
    st.Page(_lazy("hm_review"), title="HM Review", icon="👥", url_path="hm"),
    st.Page(_lazy("simulator"), title="Simulator", icon="🎭", url_path="simulator"),
    st.Page(_lazy("skill_gap"), title="Skill Gap", icon="📈", url_path="skill_gap"),
    st.Page(_lazy("company"), title="Company Insights", icon="🏢", url_path="company"),
    st.Page(_lazy("ai_insights"), title="AI Insights", icon="🤖", url_path="ai_insights"),
    st.Page(_lazy("optimizer"), title="Optimizer", icon="⚙️", url_path="optimizer"),
    st.Page(_lazy("comparison"), title="Comparison", icon="🔄", url_path="comparison"),
    st.Page(_lazy("analytics"), title="Analytics", icon="📊", url_path="analytics"),
    st.Page(_lazy("versions"), title="Versions", icon="📅", url_path="versions"),
    st.Page(_lazy("interview"), title="Interview Prep", icon="🎤", url_path="interview"),
    st.Page(_lazy("chatbot"), title="Chatbot", icon="💬", url_path="chatbot"),
    st.Page(_lazy("generator"), title="Generator", icon="✨", url_path="generator"),
    st.Page(_lazy("admin"), title="Admin", icon="🛡️", url_path="admin"),
]

QUOTES = [
    "Resume dalo, naukri pao! ATS score dekh ke mummy ko batao — 'Dekho Maa, main topper hoon!' 😄",
    "Job description match karo aur chhaa jao interview mein. CV Chacha hai na, tension mat lo! 🚀",
    "Arre bhai, resume mein keywords daalo, naukri apne aap aayegi. Yeh ATS system hai, magic nahi! ✨",
    "Interview mein jaake bolo — 'Mera resume to CV Chacha ne hi banaya hai!' Boss impressed ho jayega. 😎",
    "Resume bejho, company walon ka ATS score check karo. Agar 70+ hai to party pakka! 🎉",
    "Ek bar CV Chacha pe analysis karo, phir dekho recruiter kaise line lagate hain. 'Sir, aap to chhup ke superstar nikle!' ⭐",
    "Beta, yeh resume itna optimized hai ki Google ko bhi job lene ka man karega! 🔥",
    "Company culture dekhni hai? CV Chacha bata dega — 'Yahan pizza to milta hai, par growth bhi hai?' 🍕",
    "Skill gap analysis dekha? Ab seekh lo jo seekhna hai. Coursera kholo aur lag jao! 📚",
    "Truthfulness score 100%? Matlab aap genuine ho. Ya phir CV Chacha ko fool kar diya? 😅",
    "Job switch kar rahe ho? Pehle CV Chacha se puch lo — 'Kya main ready hoon bhai?' 🤔",
    "ATS ka range 0-100 hai. Tension mat lo, hum yahan hain! Chacha ko bulao, kaam ho jayega. 💪",
    "LinkedIn pe 'Open to Work' lagao, par pehle CV Chacha se resume optimize karwao. Phir dekho magic! 🎩",
    "HR walon ka koi bhrosa nahi. Isliye CV Chacha sab check kar leta hai — 'Pehle safety, phir naukri!' 🛡️",
    "Arre yaar, yeh JD mein kya kya maang rahe hain? Python bhi chahiye, Excel bhi chahiye... Beta, tum to chhote computer ho! 🖥️",
    "Resume mein spell check karo warna 'Manager' likh kar 'Manger' na likh do. CV Chacha pakad lega! 🔍",
    "ATS system hai buddhu, formatting nahi samajhta. Table mat daalo, warna zero score! 📊",
    "Cover letter likhna bhool gaye? Arey haan, koi nahi padhta. Sirf ATS score dekhte hain! 📝",
    "Fresher ho to bhi kya hua, confident raho. CV Chacha hai na, sab sambhal lega! 💪",
    "Experienced ho? To bhi CV Chacha se check karwa lo. Kabhi kabhi senior log bhi galti karte hain! 👴",
    "Salary negotiation ka tension mat lo. Pehle resume to shi kar lo, baaki sab theek ho jayega! 💰",
    "Ye jo tumne 'MS Excel' likha hai, iska matlab 'Mast Schedule Extra Lagao' nahi hota! 🤣",
    "Gap year hai resume mein? Chinta mat karo, CV Chacha usko bhi 'Skill Development' bana dega! 🧠",
    "Internship karte ho ya job, resume ekdum solid hona chahiye. CV Chacha beech ka rasta dikhata hai! 🛤️",
    "Tumhare resume mein 'Hardworking' likha hai? Beta, sab likhte hain. Kuch unique daalo! 🎯",
    "ATS score 40 hai? Chinta mat kar, CV Chacha ke saath 90 bhi possible hai! 🚀",
    "Referral le lo ya nahi, lekin resume to CV Chacha se optimize karwao! 📈",
    "Batch of 2024 ho? To abhi se lag jao. Placement season mein der mat karna! ⏰",
    "Ye 'Objective' waala section hai na, usko 'Summary' banao. ATS ko pasand hai! 🎯",
    "Font ka kya hai? Arial ya Calibri, simple rakho. ATS ko stylish pasand nahi! 🔤",
    "PDF me bhejo resume, Word file mat bhejo. ATS ko PDF chahiye, warna reject! 📎",
    "Skills section mein 'Cricket' mat likho jab tak Data Analyst ka job ho. Relevant rakho! 🏏",
    "Job ho ya placement, CV Chacha ka nuskha hai — ATS score 80+ aur selection fix! ✅",
    "Kya aapko pata hai? 75% resumes ATS se reject ho jate hain. CV Chacha ke saath safe raho! ⚠️",
    "Recruiter 6 second dekhta hai resume. 6 second! Isliye CV Chacha pe pehle test karo! ⏱️",
    "Apna resume CV Chacha par daalo, phir dekho kaise recruiters ke inbox mein aate hain notifications! 🔔",
    "Certificates daale hain resume mein? ATS unhe bhi count karta hai. Aur CV Chacha unhe highlight karega! 🏆",
    "Job description mein 'Team Player' likha hai to resume mein bhi daalo. Keywords se dosti rakho! 🤝",
    "Data Scientist ban na hai? To resume mein 'Machine Learning' dalo, 'Magic Learning' nahi! 🧙",
    "Resume ka font size 10 se kam mat rakho. CV Chacha ki aankh hai, padh lega! 👓",
    "Accomplishments daalo resume mein, responsibilities nahi. 'Kya kiya' likho 'kya karte the' nahi! 🏅",
    "College project likha hai? To usko bhi professional banao. CV Chacha ka suggestion lo! 🎓",
    "ATS friendly resume banana hai to tables, images, headers sab hatao. Sirf plain text! 📄",
    "Tumne company change kiya hai? To resume mein reason mat daalo. Interview mein batao! 🤫",
    "Job lag gayi? To CV Chacha ko mat bhoolo. Refer karo doston ko, unka bhi bhala hoga! 🔄",
    "Internship ke time bhi CV Chacha use karo. Early start, early success! 🚀",
    "Resume ki file name 'Resume_Final_Final2.pdf' mat rakho. Kuch professional socho! 📁",
    "ATS score check karte rehte ho? Ek baar CV Chacha pe analysis karwao aur tension free ho jao! 😌",
    "Resume ka ek page hai ya do? Fresher ho to ek, experience ho to do. Simple hai chacha! 📃",
    "Portfolio link dalna mat bhoolo. GitHub, LinkedIn, sab kuch daalo. CV Chacha unhe index karega! 🔗",
    "Recruiter ko impress karna hai? To resume mein numbers daalo. '10% increase' likho 'growth' nahi! 📊",
    "Aaj kal AI resume scan karta hai. Isliye CV Chacha ka use karo, AI ko AI se match karo! 🤖",
    "Career gap justify karo correctly. CV Chacha se puch lo kaise likhna hai! 📝",
    "Resume me photo mat lagao. ATS ko nahi chahiye tera chehra, usko chahiye skills! 🚫",
    "Hiring manager resume 10 second dekhta hai. Pehle 2 line mein impress karo! ⚡",
    "Skills section relevant rakho. Python aata hai to daalo, 'PubG' nahi chalega! 🎮",
    "Job search mein consistency sabse zaroori hai. Roz 2-3 jobs apply karo, CV Chacha ke saath! 🎯",
    "LinkedIn profile bhi optimize karo. CV Chacha resume analysis ke saath tips bhi dega! 📱",
    "Tumhara resume 'Average' hai? to 'Exceptional' banao. CV Chacha seedha rasta dikhata hai! 📈",
    "Naukri chahiye? To pehle CV Chacha ko bulao, chai pilao aur analysis karwao! ☕",
    "Ye AI kitna smart hai? ATS system tumhare resume ko rank karta hai. Smart bano, CV Chacha use karo! 🧠",
    "Fresher ho ya experienced, resume optimization sabke liye zaroori hai. Yeh beta, CV Chacha ka maamla hai! 😎",
    "Ek baar CV Chacha se check karwao, phir kisi aur ki zaroorat nahi. 'Sir, aap to ready ho!' 🏁",
    "Formatting se mat khelo. ATS ko simple pasand hai. Daal deta hai direct shortlist mein! ✅",
    "Experience ka 'ekad' nahi, detail mein likho. CV Chacha detail-oriented hai! 🔍",
    "Tumhara dream job CV Chacha ke ek click ki doori pe hai. Aaj hi analysis karwao! ✨",
    "Ye market mein competition hai, to CV Chacha ko apna secret weapon banao! 🗡️",
    "Bade bade recruiters, CV Chacha ka analysis dekhte hi offer letter bhejne lagte hain! 💌",
    "Koi resume perfect nahi hota. CV Chacha perfect banane ka formula hai! 🧪",
    "Placement season mein CV Chacha ka analysis jaroor karo. Seniors ka yahi kehna hai! 🏫",
    "Tumhari skills aur job description mein gap hai? Skill Gap Analysis karwao CV Chacha se! 🕳️",
    "Mock interview dena hai? Pehle CV Chacha se resume thik karwao, phir practice karo! 🎤",
    "CV Chacha ke saath ek baar kaam kiya to kabhi nahi bhoologe. Itna aasan hai use karna! 🤗",
    "Yeh resume tumhara brand hai. CV Chacha brand value badhane ka kaam karta hai! 💎",
    "Resume ko update karna mat bhoolo har 6 mahine mein. CV Chacha reminder dega! ⏰",
    "JOBS ka matlab? 'Just Ordered By CV Chacha' — naukri pakki hai ab! 😄",
    "Resume mein hobbies likhni hain to 'Coding' likho 'Cooking' nahi. Unless chef ban na ho! 🍳",
    "ATS ko images nahi dikhti, usko text chahiye. Infographics hatao, content rakho! 🖼️",
    "Font colour black rakho, rainbow nahi. ATS ko simple pasand hai, stylish nahi! 🌈",
    "Resume mein 'References available upon request' mat likho. Wasted space hai! 📄",
    "Job portal pe profile daalo aur CV Chacha se resume optimize karwao. Double dhamaka! 💥",
    "Placement cell mein jakar CV Chacha ka naam mat lena. Woh bhi use karenge phir! 😉",
    "Recruiter ka time 6 second hai. Isliye resume ka pehla part sabse important! 🎯",
    "Skill development karo, par resume mein bhi update karo. CV Chacha bata dega kya daalna hai! 📈",
    "ATS mein 'Summary' section sabse important hai. Wahi recruiter padhta hai pehle! 👁️",
    "Job switching normal hai, par resume mein frequency mat dikhao. Ek baar CV Chacha se discuss karo! 🔄",
    "Resume mein 'Achievements' section daalo. 'Won college cricket tournament' bhi chalega! 🏆",
    "Fresher ho to project detail mein likho. Internship nahi hai to projects se compensate karo! 💻",
    "Resume ka pdf file size 2MB se kam rakho. ATS server pe heavy file load nahi hoti! 📦",
    "LinkedIn profile URL daalo resume mein. HR directly LinkedIn check karega! 🔗",
    "Resume me 'I' pronoun mat use karo. 'Led' likho 'I led' nahi. Professional tone rakho! 🎓",
    "ATS score badhana hai to job description ke synonyms bhi daalo. CV Chacha batayega kaise! 📚",
    "Experience section mein numbers daalo. 'Managed team of 10' likho 'Managed team' nahi! 🔢",
    "Ek saath multiple jobs apply karte ho? To har job ke liye resume tweak karo. CV Chacha ka template use karo! 📝",
    "Resume me 'Soft skills' daalni hain? 'Communication', 'Leadership', 'Teamwork' — yeh sab daalo! 🤝",
    "Gap year ko negative mat samjho. Travel kiya to 'World tour', padhai ki to 'Coursework'! 🌍",
    "ATS system tumhara resume parse karta hai. Formatting galat hui to data katega. CV Chacha use karo! ⚙️",
    "College ke din mein CV Chacha use karte to aaj FAANG mein hote! Seniors ko batao! 🏢",
    "Resume ka objective section outdated hai. Summary use karo — 2-3 lines mein pitch! 🎤",
    "ATS score perfect hai? To ab interview ki taiyari karo. CV Chacha dono mein help karta hai! 🏆",
]

import random
if "ticker_selected" not in st.session_state:
    st.session_state.ticker_selected = random.sample(
        QUOTES, k=min(16, len(QUOTES))
    )

ticker_spans = "".join(
    f'<span class="ticker-item">{q}</span>'
    for _ in range(2)
    for q in st.session_state.ticker_selected
)

with st.sidebar:
    st.markdown(
        f"""
        <div style="text-align: center; padding: 1.2rem 0 0.3rem 0;">
            <img src="data:image/png;base64,{icon_b64}"
                 style="width: 48px; height: auto; filter: drop-shadow(0 0 12px rgba(204, 120, 92, 0.4));"
                 alt="CV Chacha">
            <div style="color: #faf9f5; font-family: 'Playfair Display', serif;
                       font-size: 1.5rem; font-weight: 400; letter-spacing: -0.5px; line-height: 1.2;">
                CV Chacha
            </div>
            <div style="color: #6c6a64; font-size: 0.6rem; letter-spacing: 1.5px; text-transform: uppercase; font-weight: 400; margin-top: 0.05rem;">
                by Mayank Batra
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    user_info = st.session_state.get("user_info")
    if user_info:
        role_badge = {"super_admin": "🛡️", "admin": "🔧", "user": "👤"}.get(user_info["role"], "👤")
        st.markdown(
            f"<div style='padding:0.5rem 0.8rem;background:#252320;border-radius:6px;margin:0.5rem 0;font-size:0.8rem;'>"
            f"<span style='color:#a09d96;'>{role_badge} {user_info['email']}</span><br>"
            f"<span style='color:#6c6a64;font-size:0.7rem;'>Role: {user_info['role']}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    for page in pages:
        st.page_link(page, label=page.title, icon=page.icon, use_container_width=True)

st.markdown(
    f"""
    <div style="display: flex; align-items: center; gap: 0.8rem; margin-bottom: 1rem;">
        <img src="data:image/png;base64,{icon_b64}"
             style="width: 40px; height: auto; filter: drop-shadow(0 0 8px rgba(204, 120, 92, 0.3));"
             alt="CV Chacha">
        <div style="flex:1;">
            <div style="font-family: 'Playfair Display', serif; font-size: 1.6rem; color: #141413;
                        letter-spacing: -0.5px; line-height: 1.2;">CV Chacha</div>
            <div style="color: #8e8b82; font-size: 0.65rem; letter-spacing: 1.5px; text-transform: uppercase; font-weight: 400; margin-top: 0.05rem;">by Mayank Batra</div>
        </div>
    </div>
    <div class="ticker-wrap">
        <div class="ticker-track">{ticker_spans}</div>
    </div>
    <style>
        .ticker-wrap {{
            background: #efe9de; border: 1px solid #e6dfd8; border-radius: 6px;
            padding: 0.4rem 0; margin-bottom: 1rem; overflow: hidden;
            box-sizing: border-box; position: relative; width: 100%;
        }}
        .ticker-track {{
            display: flex; white-space: nowrap; width: fit-content;
            animation: ticker-scroll 400s linear infinite;
        }}
        .ticker-item {{
            display: inline-block; padding: 0 2rem; flex-shrink: 0;
            font-family: 'Inter', sans-serif; font-size: 0.8rem; color: #6c6a64;
            font-style: italic;
        }}
        @keyframes ticker-scroll {{
            0% {{ transform: translateX(0); }}
            100% {{ transform: translateX(-50%); }}
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.session_state._page_objects = {p.url_path: p for p in pages}

nav = st.navigation(pages, position="hidden")
nav.run()
