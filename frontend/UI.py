import streamlit as st
import requests
import json
import time
import uuid
from datetime import datetime
import pandas as pd
from typing import Dict, List, Optional
import io
from PIL import Image
import base64

st.set_page_config(
    page_title="CyberGuard AI - Cybersecurity Assistant",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;500;600;700&display=swap');
:root{
  --cyber-primary:#00ff88;
  --cyber-secondary:#0088ff;
  --cyber-accent:#ff0088;
  --cyber-dark:#0a0a0a;
  --cyber-darker:#050505;
  --cyber-light:#1a1a1a;
  --cyber-muted:#88ccff;
  --cyber-text:#ffffff;
  --glass:rgba(255,255,255,0.04);
  --glass-strong:rgba(255,255,255,0.08);
  --brd:rgba(0,255,136,0.25);
  --brd-strong:rgba(0,255,136,0.5);
}
.stApp{
--primary-color: var(--cyber-primary) !important;
  color:var(--cyber-text);
  background:
    radial-gradient(1000px 500px at 10% 0%, rgba(0,255,136,0.07) 0%, rgba(0,0,0,0) 60%),
    radial-gradient(800px 400px at 100% 0%, rgba(0,136,255,0.07) 0%, rgba(0,0,0,0) 60%),
    linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
  overflow-x:hidden;
}
#MainMenu{visibility:hidden}
footer{visibility:hidden}
header{background:transparent}
.block-container{
  padding-top:1.5rem;
  padding-bottom:3rem;
}
.cy-grid{
  position:fixed;
  inset:0;
  background-image:linear-gradient(to right, rgba(255,255,255,0.04) 1px, transparent 1px),linear-gradient(to bottom, rgba(255,255,255,0.04) 1px, transparent 1px);
  background-size:40px 40px;
  mask-image:radial-gradient(ellipse at 60% -20%, rgba(0,0,0,0.7), transparent 65%);
  pointer-events:none;
  z-index:0;
}
.cy-scanline{
  position:fixed;left:0;right:0;height:2px;
  top:-2px;background:linear-gradient(90deg, transparent, rgba(0,255,136,0.7), rgba(0,136,255,0.7), transparent);
  filter:blur(0.3px);
  animation:scan 7s linear infinite;
  opacity:0.6;z-index:1;
}
@keyframes scan{
  0%{top:-2px}
  100%{top:100%}
}
.landing{
  min-height:calc(100vh - 80px);
  display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;
  gap:24px;position:relative;z-index:2;
}
.title{
  font-family:'Orbitron', monospace;
  font-size:4.2rem;line-height:1.05;font-weight:900;margin:0;
  background:linear-gradient(45deg, var(--cyber-primary), var(--cyber-secondary), var(--cyber-primary));
  background-size:200% 200%;
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;
  animation:shine 3.2s ease-in-out infinite;
  text-shadow:0 0 34px rgba(0,255,136,0.45);
}
@media (max-width:900px){ .title{font-size:3.1rem} }
@media (max-width:600px){ .title{font-size:2.6rem} }
@keyframes shine{
  0%{background-position:0% 50%}
  50%{background-position:100% 50%}
  100%{background-position:0% 50%}
}
.subtitle{
  font-family:'Rajdhani',sans-serif;
  color:var(--cyber-muted);
  font-size:1.25rem;opacity:0.95;margin-top:4px;margin-bottom:8px;
}
.under-sub{
  font-family:'Rajdhani',sans-serif;
  color:#b9cff9;opacity:0.9;font-size:1rem;letter-spacing:0.4px;
}
.features{
  display:grid;gap:18px;margin-top:22px;max-width:1100px;width:100%;
  grid-template-columns:repeat(3,minmax(0,1fr));
}
@media (max-width:980px){ .features{grid-template-columns:repeat(2,minmax(0,1fr))} }
@media (max-width:720px){ .features{grid-template-columns:repeat(1,minmax(0,1fr))} }
.card{
  background:var(--glass);
  border:1px solid var(--brd);
  border-radius:14px;
  padding:20px 18px;
  backdrop-filter:blur(10px);
  transition:transform .25s ease, border-color .25s ease, box-shadow .25s ease;
  position:relative;overflow:hidden;
}
.card::before{
  content:"";
  position:absolute;inset:-2px;
  background:conic-gradient(from 0deg, rgba(0,255,136,0.15), rgba(0,136,255,0.15), rgba(0,255,136,0.15));
  filter:blur(22px);opacity:0;transition:opacity .25s ease;
}
.card:hover::before{opacity:1}
.card:hover{
  transform:translateY(-4px);
  border-color:var(--brd-strong);
  box-shadow:0 18px 50px rgba(0,255,136,0.18);
}
.cicon{
  font-size:2rem;margin-bottom:8px;color:var(--cyber-primary)
}
.ctitle{
  font-family:'Orbitron', monospace;
  font-weight:700;font-size:1.05rem;margin-bottom:6px;color:#fff;letter-spacing:0.6px
}
.cdesc{
  font-family:'Rajdhani',sans-serif;color:#bfbfbf;font-size:0.98rem;line-height:1.55
}
.btn-wrap{
  display:flex;align-items:center;justify-content:center;margin-top:28px;margin-bottom:6px;width:100%;
}
.stButton>button{
  font-family:'Orbitron', monospace;
  font-weight:800;
  letter-spacing:1.6px;
  text-transform:uppercase;
  font-size:0.86rem;
  padding:10px;
  color:#000;
  background:linear-gradient(45deg, var(--cyber-primary), var(--cyber-secondary));
  border:none;border-radius:14px;
  box-shadow:0 14px 40px rgba(0,255,136,0.35), inset 0 0 0 1px rgba(0,0,0,0.06);
  transition:transform .18s ease, box-shadow .18s ease, filter .18s ease;
  position:relative;isolation:isolate;
}
.stButton>button:before{
  content:"";
  position:absolute;inset:-3px;border-radius:16px;
  background:radial-gradient(120px 120px at var(--mx,50%) var(--my,50%), rgba(0,255,136,0.25), rgba(0,136,255,0.18), transparent 55%);
  opacity:0;transition:opacity .2s ease;
}
.stButton>button:hover:before{opacity:1}
.stButton>button:hover{
  transform:translateY(-2px);
  box-shadow:0 20px 55px rgba(0,255,136,0.45);
  filter:saturate(1.08);
}
.stButton>button:active{transform:translateY(0)}
.stButton>button span.kbd{
  position:absolute;right:14px;top:12px;
  font-size:10px;background:rgba(0,0,0,0.45);color:#e2ffe2;
  border:1px solid rgba(255,255,255,0.15);border-radius:6px;padding:2px 5px;
}
.sidebar-content{
  font-family:'Rajdhani',sans-serif;
}
.css-1d391kg, [data-testid="stSidebar"]{
  background:linear-gradient(180deg, #0a0a0a 0%, #1a1a2e 100%);
  border-right:1px solid rgba(0,255,136,0.15);
}
.metric-card{
  background:var(--glass);
  border:1px solid var(--brd);
  border-radius:10px;padding:12px 14px;margin:6px 0
}
.status-healthy{color:var(--cyber-primary);font-weight:700}
.status-error{color:#ff4444;font-weight:700}
.status-warning{color:#ffaa00;font-weight:700}
.stTabs [data-baseweb="tab-list"]{
  gap:0.5rem;background:var(--glass);border-radius:10px;padding:6px;border:1px solid var(--brd)
}
.stTabs [data-baseweb="tab"]{
  font-family:'Orbitron', monospace;font-weight:700;background:transparent;color:#b7c7ff;border-radius:8px
}
.stTabs [data-baseweb="tab"][aria-selected="true"]{
  background:linear-gradient(45deg, var(--cyber-primary), var(--cyber-secondary));
  color:#000
}
.stTextInput input, .stTextArea textarea{
  background:rgba(255,255,255,0.06)!important;
  border:1px solid var(--brd)!important;border-radius:10px!important;color:#fff!important
}
.stSelectbox div[data-baseweb="select"]>div{
  background:rgba(255,255,255,0.06)
}
.stFileUploader{
  background:var(--glass);border:2px dashed var(--brd);border-radius:10px;padding:20px
}
.stFileUploader:hover{border-color:var(--cyber-primary);background:rgba(0,255,136,0.06)}
.chat-container{
  background:var(--glass);border-radius:12px;padding:16px;margin:10px 0;border:1px solid rgba(0,255,136,0.15)
}
.chat-message{
  background:rgba(0,136,255,0.12);
  border-left:4px solid var(--cyber-secondary);
  padding:1rem;margin:1rem 0;border-radius:10px;font-family:'Rajdhani',sans-serif
}
.chat-response{
  background:rgba(0,255,136,0.12);
  border-left:4px solid var(--cyber-primary);
  padding:1rem;margin:1rem 0;border-radius:10px;font-family:'Rajdhani',sans-serif
}
.rule{
  height:1px;background:linear-gradient(90deg, transparent, rgba(0,255,136,0.25), transparent);
  margin:12px 0
}
.badge{
  display:inline-flex;gap:8px;align-items:center;
  border:1px dashed var(--brd);border-radius:999px;padding:6px 12px;background:rgba(0,255,136,0.06);font-family:'Rajdhani',sans-serif
}
.kpis{
  display:grid;gap:12px;grid-template-columns:repeat(4,minmax(0,1fr))
}
@media (max-width:1100px){ .kpis{grid-template-columns:repeat(2,minmax(0,1fr))} }
@media (max-width:640px){ .kpis{grid-template-columns:repeat(1,minmax(0,1fr))} }
.kpi{
  background:var(--glass);border:1px solid var(--brd);border-radius:12px;padding:16px
}
.kpi h4{margin:0;font-family:'Orbitron', monospace;font-size:0.95rem;color:#eafef5}
.kpi p{margin:6px 0 0;font-size:1.35rem;font-weight:800;color:#fff}
.small{
  color:#c8d6ff;font-size:0.9rem;font-family:'Rajdhani',sans-serif
}
.footer{
  margin-top:28px;opacity:0.9;color:#b8c7ff;text-align:center;font-size:0.95rem
}
hr{border:none;height:1px;background:linear-gradient(90deg, transparent, rgba(0,255,136,0.22), transparent)}
.tooltip{
  display:inline-block;border-bottom:1px dotted rgba(255,255,255,0.4);cursor:help
}
.stDownloadButton>button{
  border-radius:10px;border:1px solid var(--brd);
  background:rgba(0,255,136,0.12);color:#eafff7
}
.stDownloadButton>button:hover{
  background:rgba(0,255,136,0.18)
}
.glow{
  text-shadow:0 0 16px rgba(0,255,136,0.35), 0 0 4px rgba(0,136,255,0.25)
}
.stAlert{
  background:rgba(0,0,0,0.35)
}
.cy-divider{
  width:100%;height:2px;background:linear-gradient(90deg, transparent, rgba(0,136,255,0.35), rgba(0,255,136,0.35), transparent);
  border-radius:999px;margin:12px 0
}
div[data-baseweb="slider"]{
  padding: .75rem 1rem;
  background: var(--glass);
  border: 1px solid var(--brd);
  border-radius: 12px;
  backdrop-filter: blur(8px);
  box-shadow: 0 0 12px rgba(0,255,136,0.22);
}


div[data-baseweb="slider"] > div{
  height: 8px;
}


div[data-baseweb="slider"] > div > div{
  height: 8px;
  border-radius: 4px;
  background: linear-gradient(90deg, var(--cyber-primary), var(--cyber-secondary));
  background-size: 200% 200%;
  animation: cy-neon-shift 6s ease infinite;
  box-shadow: 0 0 10px rgba(0,255,136,0.25);
}


div[data-baseweb="slider"] [role="slider"]{
  height: 24px;
  width: 24px;
  border-radius: 50%;
  background: var(--cyber-primary);
  border: 2px solid var(--cyber-secondary);
  box-shadow: 0 0 16px rgba(0,255,136,0.45), 0 0 10px rgba(0,136,255,0.35);
  transition: transform .15s ease, box-shadow .15s ease, filter .15s ease;
}
div[data-baseweb="slider"] [role="slider"]:hover{
  transform: translateY(-1px) scale(1.05);
  filter: saturate(1.05);
}
div[data-baseweb="slider"] [role="slider"]:active{
  transform: scale(1.0);
}

div[data-testid="stSliderThumbValue"]{
  font-family: 'Orbitron', monospace;
  color: var(--cyber-primary);
  font-weight: 800;
  text-shadow: 0 0 8px rgba(0,255,136,0.4);
}

label[data-testid="stWidgetLabel"]{
  font-family: 'Orbitron', monospace;
  color: var(--cyber-muted);
  font-weight: 800;
  letter-spacing: .4px;
}

@keyframes cy-neon-shift{
  0%{background-position: 0% 50%}
  50%{background-position: 100% 50%}
  100%{background-position: 0% 50%}
}

:root, .stApp{
  --primary-color: var(--cyber-primary) !important;
}

/* cyber checkbox wrapper + label */
div[data-baseweb="checkbox"]{
  display:flex;align-items:center;gap:.55rem;color:var(--cyber-muted) !important;
}
div[data-baseweb="checkbox"] > label{
  display:flex;align-items:center;gap:.6rem;
  font-family:'Orbitron', monospace;font-weight:700;letter-spacing:.4px;
  color:var(--cyber-muted) !important; cursor:pointer;
}

/* the square box */
div[data-baseweb="checkbox"] [role="checkbox"]{
  position:relative;flex:0 0 auto;
  width:22px;height:22px;border-radius:6px;
  background:var(--glass) !important;
  border:2px solid var(--brd) !important;
  box-shadow:0 0 8px rgba(0,255,136,.25);
  transition:all .18s ease;
}
div[data-baseweb="checkbox"] [role="checkbox"]:hover{
  transform:translateY(-1px);filter:saturate(1.05)
}

/* checked state = same animated gradient as your slider */
div[data-baseweb="checkbox"] [role="checkbox"][aria-checked="true"]{
  background:linear-gradient(90deg, var(--cyber-primary), var(--cyber-secondary)) !important;
  background-size:200% 200%; animation:cy-neon-shift 6s ease infinite;
  border-color:var(--cyber-primary) !important;
  box-shadow:0 0 14px rgba(0,255,136,.45),0 0 10px rgba(0,136,255,.35);
  color:#000 !important; /* prevents currentColor red fallback */
}

div[data-baseweb="checkbox"] [role="checkbox"][aria-checked="true"]::after{
  content:"✓"; position:absolute; inset:0;
  display:flex; align-items:center; justify-content:center;
  font-size:14px; font-weight:900; color:#000;
  text-shadow:0 0 6px rgba(0,0,0,.35);
}
div[data-baseweb="checkbox"] [role="checkbox"] svg{display:none !important;}
            
</style>
<div class="cy-grid"></div>
<div class="cy-scanline"></div>
<script>
document.addEventListener('mousemove',function(e){
  const btns=document.querySelectorAll('.stButton>button');
  btns.forEach(b=>{
    const r=b.getBoundingClientRect();
    const mx=((e.clientX - r.left)/r.width)*100;
    const my=((e.clientY - r.top)/r.height)*100;
    b.style.setProperty('--mx', mx+'%');
    b.style.setProperty('--my', my+'%');
  });
});
</script>
""", unsafe_allow_html=True)

API_BASE_URL = "http://127.0.0.1:8000"

if "app_started" not in st.session_state:
    st.session_state.app_started = False
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "api_status" not in st.session_state:
    st.session_state.api_status = "unknown"
if "landing_art" not in st.session_state:
    st.session_state.landing_art = None

def check_api_health() -> Dict:
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            st.session_state.api_status = "healthy"
            return response.json()
        else:
            st.session_state.api_status = "error"
            return {"status": "error", "message": f"HTTP {response.status_code}"}
    except requests.exceptions.ConnectionError:
        st.session_state.api_status = "offline"
        return {"status": "offline", "message": "Cannot connect to API"}
    except Exception as e:
        st.session_state.api_status = "error"
        return {"status": "error", "message": str(e)}

def send_chat_message(message: str, include_sources: bool = True, max_sources: int = 3) -> Dict:
    try:
        payload = {
            "message": message,
            "session_id": st.session_state.session_id,
            "include_sources": include_sources,
            "max_sources": max_sources
        }
        response = requests.post(f"{API_BASE_URL}/chat", json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}", "details": response.text}
    except Exception as e:
        return {"error": f"Connection Error: {str(e)}"}

def upload_file_to_api(uploaded_file) -> Dict:
    try:
        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
        response = requests.post(f"{API_BASE_URL}/upload-document", files=files, timeout=90)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Upload Error: {response.status_code}", "details": response.text}
    except Exception as e:
        return {"error": f"Upload Error: {str(e)}"}

def upload_text_to_api(text: str, filename: str, metadata: Dict = None) -> Dict:
    try:
        payload = {"filename": filename, "content": text, "document_type": "text", "metadata": metadata or {}}
        response = requests.post(f"{API_BASE_URL}/upload-text", json=payload, timeout=90)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Upload Error: {response.status_code}", "details": response.text}
    except Exception as e:
        return {"error": f"Upload Error: {str(e)}"}

def get_system_stats() -> Dict:
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Stats Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Stats Error: {str(e)}"}

def search_documents(query: str, top_k: int = 5) -> Dict:
    try:
        params = {"query": query, "top_k": top_k}
        response = requests.get(f"{API_BASE_URL}/search", params=params, timeout=20)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Search Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Search Error: {str(e)}"}

def byte_image_to_base64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def show_landing_page():
    st.markdown(
        """
        <section class="landing">
          <h1 class="title">CyberGuard AI</h1>
          <div class="subtitle">Advanced Cybersecurity Intelligence Assistant</div>
          <div class="under-sub">Threat intelligence • Vulnerability analysis • Knowledge graph citations</div>
          <div class="features">
            <div class="card">
              <div class="cicon">🤖</div>
              <div class="ctitle">AI-Powered Analysis</div>
              <div class="cdesc">Dynamic reasoning over your security corpus, combining retrieval-augmented generation with policy-aware answers.</div>
            </div>
            <div class="card">
              <div class="cicon">🔍</div>
              <div class="ctitle">Threat Intelligence</div>
              <div class="cdesc">Search, cluster, and explore IoCs, CVEs, TTPs, and reports with semantically ranked evidence.</div>
            </div>
            <div class="card">
              <div class="cicon">📚</div>
              <div class="ctitle">Knowledge Base</div>
              <div class="cdesc">Curate documents and notes with source-grounded insights and reproducible references.</div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True
    )
    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        if st.button("Start Security Scan", key="start_button"):
            st.session_state.app_started = True
            st.rerun()
    st.markdown('<div class="footer">By proceeding you agree to responsible use of CyberGuard AI for defensive security purposes.</div>', unsafe_allow_html=True)

def sidebar_panel():
    with st.sidebar:
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        st.markdown("## CyberGuard AI")
        st.markdown('<div class="cy-divider"></div>', unsafe_allow_html=True)
        st.markdown("### System Status")
        health_data = check_api_health()
        if st.session_state.api_status == "healthy":
            st.markdown('<p class="status-healthy">ONLINE & SECURE</p>', unsafe_allow_html=True)
            with st.expander("Health Details"):
                st.json(health_data)
        elif st.session_state.api_status == "offline":
            st.markdown('<p class="status-error">OFFLINE</p>', unsafe_allow_html=True)
            st.warning("Backend server not responding")
        else:
            st.markdown('<p class="status-error">ERROR</p>', unsafe_allow_html=True)
            st.error(health_data.get("message", "Unknown error"))
        st.markdown('<div class="cy-divider"></div>', unsafe_allow_html=True)
        if st.session_state.api_status == "healthy":
            st.markdown("### System Metrics")
            stats = get_system_stats()
            if "error" not in stats:
                st.markdown(
                    f"""
                    <div class="metric-card"><strong>📄 Documents:</strong> {stats.get("total_documents", 0)}</div>
                    <div class="metric-card"><strong>🔍 Data Chunks:</strong> {stats.get("total_chunks", 0)}</div>
                    <div class="metric-card"><strong>👥 Active Sessions:</strong> {stats.get("chat_sessions", 0)}</div>
                    <div class="metric-card"><strong>⏱️ Uptime:</strong> {stats.get("uptime", 0):.1f}s</div>
                    """,
                    unsafe_allow_html=True,
                )
        st.markdown('<div class="cy-divider"></div>', unsafe_allow_html=True)
        st.markdown("### Analysis Settings")
        include_sources = st.checkbox("Include Source References", value=True)
        max_sources = st.slider("Max Sources", 1, 10, 3)
        st.markdown('<div class="cy-divider"></div>', unsafe_allow_html=True)
        st.markdown("### Controls")
        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.success("Chat history cleared")
        if st.button("Return to Home", use_container_width=True):
            st.session_state.app_started = False
            st.rerun()
        st.markdown('<div class="cy-divider"></div>', unsafe_allow_html=True)
        st.markdown("### Session Info")
        st.markdown(
            f"""
            <div class="metric-card"><strong>Session:</strong> {st.session_state.session_id[:8]}...</div>
            <div class="metric-card"><strong>Messages:</strong> {len(st.session_state.chat_history)}</div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)
    return include_sources, max_sources

def chat_tab(include_sources: bool, max_sources: int):
    if st.session_state.api_status != "healthy":
        st.error("SYSTEM OFFLINE - Cannot process security analysis")
        st.info("Ensure the backend security server is running and accessible.")
        return
    st.markdown("### AI Security Analyst")
    st.markdown("Ask questions about cybersecurity threats, vulnerabilities, and best practices.")
    if st.session_state.chat_history:
        st.markdown("### Analysis History")
        for i, chat in enumerate(st.session_state.chat_history):
            st.markdown(
                f"""
                <div class="chat-message">
                    <strong>You:</strong><br>
                    {chat.get("question","")}
                </div>
                """,
                unsafe_allow_html=True,
            )
            if "error" in chat:
                st.markdown(
                    f"""
                    <div class="chat-response">
                        <strong>Analysis Error:</strong><br>
                        {chat["error"]}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div class="chat-response">
                        <strong>AI Analysis:</strong><br>
                        {chat.get("response","")}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                c1, c2 = st.columns(2)
                with c1:
                    st.caption(f"⏱️ Analysis Time: {chat.get('response_time', 0)}s")
                with c2:
                    st.caption(f"📅 Timestamp: {chat.get('timestamp', '')}")
                if chat.get("sources"):
                    with st.expander(f"📚 Intelligence Sources ({len(chat['sources'])})"):
                        for source in chat["sources"]:
                            st.markdown(f"**🔍 Source {source.get('rank','?')}** — Relevance: {source.get('similarity_score','?')}")
                            st.text_area(
                                f"Content Preview ({source.get('content_length','?')} chars)",
                                source.get("content",""),
                                height=120,
                                key=f"src_{i}_{source.get('rank','x')}",
                            )
                            st.markdown("---")
    user_input = st.chat_input("Enter your cybersecurity question...")
    if user_input:
        with st.spinner("Analyzing security query..."):
            response = send_chat_message(user_input, include_sources=include_sources, max_sources=max_sources)
        if "error" in response:
            entry = {"question": user_input, "error": response["error"], "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        else:
            entry = {
                "question": user_input,
                "response": response.get("response"),
                "sources": response.get("sources", []),
                "response_time": response.get("response_time"),
                "timestamp": response.get("timestamp"),
            }
        st.session_state.chat_history.append(entry)
        st.rerun()

def upload_tab():
    st.markdown("### 📄 Intelligence Upload Center")
    if st.session_state.api_status != "healthy":
        st.error("UPLOAD SYSTEM OFFLINE")
        return
    st.markdown("#### Upload Security Documents")
    uploaded_file = st.file_uploader("Choose intelligence files", type=["txt", "pdf", "md", "csv", "json", "xml"], help="Supported: TXT, PDF, MD, CSV, JSON, XML")
    if uploaded_file is not None:
        st.info(f"File: {uploaded_file.name} ({uploaded_file.size:,} bytes)")
        if st.button("Process Intelligence", use_container_width=True):
            with st.spinner("Processing security intelligence..."):
                result = upload_file_to_api(uploaded_file)
            if "error" in result:
                st.error(f"Processing failed: {result['error']}")
            else:
                st.success("Intelligence processed successfully")
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("📋 Document ID", result.get("document_id","")[:8] + "...")
                with c2:
                    st.metric("🧩 Data Chunks", result.get("chunks_created", 0))
                with c3:
                    st.metric("⚡ Processing Time", f"{result.get('processing_time',0)}s")
    st.markdown("---")
    st.markdown("#### Direct Text Intelligence")
    text_filename = st.text_input("Intelligence File Name", placeholder="threat_report.txt")
    text_content = st.text_area("Intelligence Content", height=220, placeholder="Paste threat intelligence, security reports, or vulnerability data here...")
    if st.button("Process Text Intelligence", use_container_width=True):
        if not text_filename or not text_content:
            st.error("Provide both filename and content")
        else:
            with st.spinner("Processing text intelligence..."):
                result = upload_text_to_api(text_content, text_filename)
            if "error" in result:
                st.error(f"Processing failed: {result['error']}")
            else:
                st.success("Text intelligence processed successfully")
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("📋 Document ID", result.get("document_id","")[:8] + "...")
                with c2:
                    st.metric("🧩 Data Chunks", result.get("chunks_created", 0))
                with c3:
                    st.metric("⚡ Processing Time", f"{result.get('processing_time',0)}s")

def search_tab():
    st.markdown("### 🔍 Threat Intelligence Search")
    if st.session_state.api_status != "healthy":
        st.error("SEARCH SYSTEM OFFLINE")
        return
    st.markdown("Search through processed security intelligence without generating responses")
    c1, c2 = st.columns([3, 1])
    with c1:
        search_query = st.text_input("Search Query", placeholder="malware, vulnerability, attack vector, etc.")
    with c2:
        search_top_k = st.number_input("Results", min_value=1, max_value=20, value=5)
    if st.button("Execute Search", use_container_width=True) and search_query:
        with st.spinner("Scanning intelligence database..."):
            results = search_documents(search_query, search_top_k)
        if "error" in results:
            st.error(f"Search failed: {results['error']}")
        else:
            st.success(f"Found {results.get('total_found',0)} intelligence matches for: {results.get('query','')}")
            if results.get("results"):
                for r in results["results"]:
                    with st.expander(f"🎯 Result {r.get('rank','?')} — Relevance: {r.get('similarity_score','?')}"):
                        st.markdown(f"**🆔 Document ID:** `{r.get('document_id','')}`")
                        st.markdown(f"**📏 Content Length:** {r.get('content_length',0):,} characters")
                        st.markdown("**📄 Intelligence Preview:**")
                        st.text_area("Content", r.get("content",""), height=180, key=f"res_{r.get('rank','x')}")
            else:
                st.info("No matching intelligence found")

def admin_tab():
    st.markdown("### ⚙️ System Administration Panel")
    if st.session_state.api_status != "healthy":
        st.error("ADMIN PANEL OFFLINE")
        return
    st.markdown("#### Bulk Intelligence Processing")
    st.info("Process all documents from the ./data/raw_documents/ directory")
    if st.button("Process All Documents", use_container_width=True):
        with st.spinner("Processing bulk intelligence..."):
            try:
                response = requests.post(f"{API_BASE_URL}/admin/process-documents", timeout=180)
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"{result.get('message','Completed')}")
                    if result.get("status") == "success":
                        st.metric("🧩 Chunks Processed", result.get("chunks_processed", 0))
                else:
                    st.error(f"Processing failed: HTTP {response.status_code}")
            except Exception as e:
                st.error(f"Processing failed: {str(e)}")
    st.markdown("---")
    st.markdown("#### Export Intelligence Data")
    st.info("Export processed intelligence data to CSV or JSON format")
    export_format = st.selectbox("Export Format", ["CSV", "JSON"])
    if st.button("Export Data", use_container_width=True):
        with st.spinner("Generating export file..."):
            try:
                response = requests.get(f"{API_BASE_URL}/admin/export-data", timeout=90)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        if export_format == "CSV":
                            df = pd.DataFrame(data.get("data", []))
                            csv = df.to_csv(index=False)
                            st.download_button(
                                label="Download CSV",
                                data=csv,
                                file_name=f"cyberguard_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                            st.success("Data exported as CSV")
                        else:
                            json_data = json.dumps(data.get("data", []), indent=2)
                            st.download_button(
                                label="Download JSON",
                                data=json_data,
                                file_name=f"cyberguard_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json",
                                use_container_width=True
                            )
                            st.success("Data exported as JSON")
                    else:
                        st.error(f"Export failed: {data.get('message', 'Unknown error')}")
                else:
                    st.error(f"Export failed: HTTP {response.status_code}")
            except Exception as e:
                st.error(f"Export failed: {str(e)}")
    st.markdown("---")
    st.markdown("#### Clear Intelligence Database")
    st.warning("This will permanently delete all processed intelligence data.")
    clear_confirm = st.checkbox("Confirm Database Clear", value=False)
    if st.button("Clear Database", use_container_width=True, disabled=not clear_confirm):
        with st.spinner("Clearing intelligence database..."):
            try:
                response = requests.post(f"{API_BASE_URL}/admin/clear-database", timeout=90)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "success":
                        st.success("Intelligence database cleared successfully")
                        st.metric("🧩 Documents Removed", result.get("documents_removed", 0))
                    else:
                        st.error(f"Clear failed: {result.get('message', 'Unknown error')}")
                else:
                    st.error(f"Clear failed: HTTP {response.status_code}")
            except Exception as e:
                st.error(f"Clear failed: {str(e)}")

def overview_panel():
    st.markdown("### Overview")
    st.markdown("System overview and quick insights.")
    cols = st.columns(4)
    with cols[0]:
        st.markdown('<div class="kpi"><h4>Indexed Documents</h4><p>—</p><div class="small">Synchronized corpus</div></div>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown('<div class="kpi"><h4>Knowledge Chunks</h4><p>—</p><div class="small">Vectorized segments</div></div>', unsafe_allow_html=True)
    with cols[2]:
        st.markdown('<div class="kpi"><h4>Active Sessions</h4><p>—</p><div class="small">Concurrent chats</div></div>', unsafe_allow_html=True)
    with cols[3]:
        st.markdown('<div class="kpi"><h4>Uptime</h4><p>—</p><div class="small">Service availability</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="cy-divider"></div>', unsafe_allow_html=True)

def show_chat_interface():
    include_sources, max_sources = sidebar_panel()
    st.markdown("# CyberGuard AI Assistant")
    st.markdown("*Advanced Cybersecurity Intelligence & Threat Analysis Platform*", unsafe_allow_html=True)
    overview_panel()
    tab_chat, tab_upload, tab_search, tab_admin = st.tabs(["Chat Analysis", "Upload Intel", "Threat Search", "Admin Panel"])
    with tab_chat:
        chat_tab(include_sources, max_sources)
    with tab_upload:
        upload_tab()
    with tab_search:
        search_tab()
    with tab_admin:
        admin_tab()
    st.markdown('<div class="footer">© CyberGuard AI • Defensive security tooling • All rights reserved</div>', unsafe_allow_html=True)

def main():
    if not st.session_state.app_started:
        show_landing_page()
    else:
        show_chat_interface()

if __name__ == "__main__":
    main()
