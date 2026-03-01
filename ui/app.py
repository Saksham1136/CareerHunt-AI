"""
ui/app.py — AI Job Seeker (Final Clean Version)
Fixes:
  1. Model updated to llama-3.1-8b-instant
  2. Results stored in session_state — PDF/DOCX buttons never refresh page
  3. PDFs pre-generated right after pipeline runs, download button always ready
  4. ATS Keywords section added per job search
"""

import streamlit as st
import sys, os, json
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

st.set_page_config(page_title="CareerHunt AI", page_icon="🤖",
                   layout="wide", initial_sidebar_state="expanded")

from database.db_manager import init_db
from auth.auth_manager import seed_admin_if_needed
init_db()
seed_admin_if_needed()

from config.settings import GROQ_API_KEY
from auth.auth_manager import (
    is_authenticated, is_admin, login_user, logout_user,
    register_user, validate_registration, get_current_username
)
from database.db_manager import (
    get_user_by_id, update_user_profile,
    get_user_job_searches, delete_job_search,
    get_user_resumes, delete_resume_version,
    get_user_interview_sessions, delete_interview_session,
    save_job_search, save_resume_version, save_interview_session,
    get_all_users, get_admin_stats, get_recent_activity,
    toggle_user_active, log_activity
)
from tools.resume_parser import parse_resume_from_upload

# ── CSS ──
st.markdown("""
<style>
.banner{background:linear-gradient(135deg,#1e3a5f,#2e74b5);color:white;
        padding:1.4rem 2rem;border-radius:12px;margin-bottom:1.5rem;}
.banner h1{color:white;margin:0;font-size:1.85rem;}
.banner p{color:#d0e4f5;margin:.3rem 0 0;font-size:.9rem;}
.admin-banner{background:linear-gradient(135deg,#1a1a2e,#c0392b);color:white;
              padding:1.2rem 2rem;border-radius:12px;margin-bottom:1.5rem;}
.admin-banner h2{color:white;margin:0;}
.admin-banner p{color:#f5c6cb;margin:.3rem 0 0;}
.score-high{color:#27ae60;font-weight:bold;font-size:1.4rem;}
.score-mid{color:#f39c12;font-weight:bold;font-size:1.4rem;}
.score-low{color:#e74c3c;font-weight:bold;font-size:1.4rem;}
.kw-match{display:inline-block;background:#eafaf1;color:#1a7a3e;
          padding:3px 10px;border-radius:12px;margin:3px;font-size:.82rem;font-weight:500;}
.kw-miss{display:inline-block;background:#fdf0ef;color:#c0392b;
         padding:3px 10px;border-radius:12px;margin:3px;font-size:.82rem;font-weight:500;}
.kw-ats{display:inline-block;background:#eef4ff;color:#1a3a8f;
        padding:3px 10px;border-radius:12px;margin:3px;font-size:.82rem;font-weight:500;
        border:1px solid #c0d0f0;}
.kw-hot{display:inline-block;background:#fff3e0;color:#b85c00;
        padding:3px 10px;border-radius:12px;margin:3px;font-size:.85rem;font-weight:600;
        border:1px solid #f0c080;}
.block-container{padding-top:1rem;}
.stExpander{border:1px solid #e0e7ef!important;border-radius:8px!important;}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════
# PDF GENERATORS  (defined first, used later)
# ════════════════════════════════════════════

def generate_interview_pdf(iv_data: dict, role: str) -> bytes:
    """Returns PDF as bytes (no file path needed — avoids disk/refresh issues)."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, PageBreak
        from reportlab.lib.enums import TA_CENTER
        import io
    except ImportError:
        raise ImportError("reportlab not installed. Run: pip install reportlab")

    buf   = io.BytesIO()
    doc   = SimpleDocTemplate(buf, pagesize=A4,
                               leftMargin=2*cm, rightMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
    NAVY  = colors.HexColor("#1e3a5f")
    BLUE  = colors.HexColor("#2e74b5")
    GRAY  = colors.HexColor("#333333")
    GREEN = colors.HexColor("#1a7a3e")
    styles = getSampleStyleSheet()
    def ps(name, parent="Normal", **kw):
        return ParagraphStyle(name, parent=styles[parent], **kw)

    T  = ps("T",  "Title",   fontSize=22, textColor=NAVY, spaceAfter=4, alignment=TA_CENTER)
    SB = ps("SB", "Normal",  fontSize=11, textColor=BLUE, spaceAfter=4, alignment=TA_CENTER)
    H1 = ps("H1", "Heading1",fontSize=13, textColor=NAVY, spaceBefore=12, spaceAfter=4)
    Q  = ps("Q",  "Normal",  fontSize=11, textColor=NAVY, fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=3)
    A  = ps("A",  "Normal",  fontSize=10.5, textColor=GRAY, leftIndent=14, leading=15, spaceAfter=3)
    TI = ps("TI", "Normal",  fontSize=10, textColor=GREEN, fontName="Helvetica-Oblique", leftIndent=14, spaceAfter=8)
    BU = ps("BU", "Normal",  fontSize=10.5, textColor=GRAY, leftIndent=16, leading=14, spaceAfter=2)

    def hr(thickness=0.5, color=BLUE):
        return HRFlowable(width="100%", thickness=thickness, color=color)

    story = [Spacer(1,.8*cm)]
    story += [Paragraph("Interview Preparation Guide", T),
              Paragraph(f"Role: {role}  ·  Domain: {iv_data.get('domain','')}  ·  Level: {iv_data.get('seniority','mid-level').title()}", SB),
              Paragraph(f"Generated: {datetime.now().strftime('%d %B %Y')}", SB),
              Spacer(1,.4*cm), hr(2, NAVY), Spacer(1,.4*cm)]

    # Talking points
    if iv_data.get("key_talking_points"):
        story += [Paragraph("Key Talking Points", H1), hr()]
        for tp in iv_data["key_talking_points"]:
            story.append(Paragraph(f"✦  {tp}", BU))
        story.append(Spacer(1,.3*cm))

    # Technical
    tech = iv_data.get("technical_questions",[])
    if tech:
        story += [Paragraph("Technical Interview Questions", H1), hr()]
        for i,qa in enumerate(tech,1):
            story.append(Paragraph(f"Q{i}.  {qa.get('question','')}", Q))
            story.append(Paragraph(f"<b>Answer:</b>  {qa.get('answer','')}", A))
            if qa.get("follow_up"):
                story.append(Paragraph(f"Follow-up:  {qa['follow_up']}", A))
            if qa.get("tip"):
                story.append(Paragraph(f"💡  Tip:  {qa['tip']}", TI))
            story.append(hr(.25, colors.HexColor("#dddddd")))

    story.append(PageBreak())

    # Behavioral
    beh = iv_data.get("behavioral_questions",[])
    if beh:
        story += [Paragraph("Behavioral Questions (STAR Format)", H1), hr()]
        for i,qa in enumerate(beh,1):
            story.append(Paragraph(f"B{i}.  {qa.get('question','')}", Q))
            story.append(Paragraph(f"<b>STAR Answer:</b>  {qa.get('answer','')}", A))
            if qa.get("tip"):
                story.append(Paragraph(f"💡  Tip:  {qa['tip']}", TI))
            story.append(hr(.25, colors.HexColor("#dddddd")))

    # System Design
    sd = iv_data.get("system_design_questions",[])
    if sd:
        story += [Spacer(1,.3*cm), Paragraph("System Design Questions", H1), hr()]
        for i,qa in enumerate(sd,1):
            story.append(Paragraph(f"SD{i}.  {qa.get('question','')}", Q))
            steps = qa.get("approach",[])
            if isinstance(steps, str): steps = [steps]
            for s in steps:
                story.append(Paragraph(f"  →  {s}", BU))
            if qa.get("key_concepts"):
                story.append(Paragraph(f"Key concepts tested:  {qa['key_concepts']}", TI))
            story.append(Spacer(1,.2*cm))

    # Prep tips
    tips = iv_data.get("preparation_tips",[])
    if tips:
        story += [PageBreak(), Paragraph("Preparation Tips", H1), hr()]
        for tip in tips:
            story.append(Paragraph(f"•  {tip}", BU))

    story += [Spacer(1,1*cm), hr(1,NAVY),
              Paragraph("Generated by AI Job Seeker · Powered by Groq LLaMA 3.1", SB)]

    doc.build(story)
    return buf.getvalue()


def generate_ats_keywords_for_role(role: str, jobs: list) -> dict:
    """
    Extract and categorize ATS keywords from job search results.
    Returns: {must_have, good_to_have, soft_skills, tools}
    """
    from collections import Counter
    import re

    all_skills = []
    all_text   = ""
    for job in jobs:
        all_skills.extend(job.get("skills_required", []))
        all_text += " " + job.get("description", "").lower()

    # Count skill frequency across jobs
    skill_counter = Counter(s.strip() for s in all_skills if s.strip())

    # Categorize
    tech_tools   = {"docker","kubernetes","aws","gcp","azure","git","linux","jenkins",
                    "terraform","kafka","redis","nginx","postgresql","mysql","mongodb",
                    "elasticsearch","spark","airflow","mlflow","fastapi","django","flask",
                    "react","nodejs","typescript","graphql","tableau","powerbi"}
    soft_kws     = {"communication","leadership","teamwork","problem-solving","agile",
                    "scrum","collaboration","ownership","mentoring","stakeholder"}

    must_have    = []
    good_to_have = []
    tools        = []
    soft_skills  = []

    for skill, count in skill_counter.most_common(40):
        sl = skill.lower()
        if any(s in sl for s in soft_kws):
            soft_skills.append(skill)
        elif any(s in sl for s in tech_tools):
            tools.append(skill)
        elif count >= max(2, len(jobs)//2):
            must_have.append(skill)
        else:
            good_to_have.append(skill)

    # Also scan description text for important keywords not in skills list
    important_kws = ["machine learning","deep learning","nlp","computer vision",
                     "data pipeline","rest api","microservices","ci/cd","unit testing",
                     "system design","distributed systems","a/b testing","feature engineering",
                     "model deployment","data warehouse","etl","data modeling"]
    for kw in important_kws:
        if kw in all_text and kw.title() not in must_have + good_to_have:
            good_to_have.append(kw.title())

    return {
        "must_have":    must_have[:12],
        "good_to_have": good_to_have[:12],
        "tools":        tools[:12],
        "soft_skills":  soft_skills[:8],
        "total_jobs_analyzed": len(jobs)
    }


# ════════════════════════════════════════════
# LOGIN PAGE
# ════════════════════════════════════════════
def show_login_page():
    _, col, _ = st.columns([1,2,1])
    with col:
        st.markdown("""
        <div style="text-align:center;padding:2rem 0 1.5rem;">
            <div style="font-size:3rem;">🤖</div>
            <h1 style="color:#1e3a5f;margin:0;">CareerHunt AI</h1>
            <p style="color:#666;margin-top:.3rem;">Your multi-agent career companion</p>
        </div>""", unsafe_allow_html=True)

        login_tab, signup_tab = st.tabs(["🔑 Login", "✨ Create Account"])
        with login_tab:
            st.markdown("### Welcome back!")
            with st.form("login_form"):
                uname = st.text_input("Username", placeholder="Enter your username")
                pwd   = st.text_input("Password", type="password", placeholder="Enter your password")
                if st.form_submit_button("🔑 Login", use_container_width=True, type="primary"):
                    if not uname or not pwd:
                        st.error("Please enter both fields.")
                    else:
                        with st.spinner("Authenticating..."):
                            ok, msg = login_user(uname, pwd)
                        if ok: st.success(msg); st.rerun()
                        else:  st.error(f"❌ {msg}")
            st.markdown('<div style="text-align:center;color:#888;font-size:.82rem;">Default admin: <code>admin</code> / <code>admin123</code></div>', unsafe_allow_html=True)

        with signup_tab:
            st.markdown("### Create your free account")
            with st.form("signup_form", clear_on_submit=True):
                fn = st.text_input("Full Name",  placeholder="e.g. Saksham Singh")
                nu = st.text_input("Username *", placeholder="letters, numbers, _ only")
                ne = st.text_input("Email *",    placeholder="you@email.com")
                c1,c2 = st.columns(2)
                with c1: p1 = st.text_input("Password *",         type="password", placeholder="Min 6 chars")
                with c2: p2 = st.text_input("Confirm Password *", type="password")
                if st.form_submit_button("✨ Create Account", use_container_width=True, type="primary"):
                    ok, err = validate_registration(nu, ne, p1, p2)
                    if not ok: st.error(f"❌ {err}")
                    else:
                        ok2, msg2 = register_user(nu, ne, p1, fn)
                        if ok2: st.success(f"✅ {msg2} Switch to Login tab."); st.balloons()
                        else:   st.error(f"❌ {msg2}")
        st.markdown('<div style="text-align:center;margin-top:1.5rem;color:#aaa;font-size:.78rem;">🔒 Passwords bcrypt-hashed · Data in local SQLite</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════
# DASHBOARD PAGE
# ════════════════════════════════════════════
def show_dashboard():
    uid  = st.session_state.get("user_id")
    user = get_user_by_id(uid)
    if not user: st.error("Session expired. Please log in again."); return

    st.markdown(f"""
    <div class="banner">
        <h1>👋 Welcome, {user['full_name'] or user['username']}!</h1>
        <p>@{user['username']} · {user['email']} ·
           <span style="background:#ffffff33;padding:2px 8px;border-radius:10px;font-size:.78rem;">
               {user['role'].upper()}</span></p>
    </div>""", unsafe_allow_html=True)

    searches   = get_user_job_searches(uid)
    resumes    = get_user_resumes(uid)
    interviews = get_user_interview_sessions(uid)

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("🔍 Job Searches",       len(searches))
    c2.metric("📄 Resume Versions",    len(resumes))
    c3.metric("🎤 Interview Sessions", len(interviews))
    best = max((r["ats_score_after"] for r in resumes), default=0)
    c4.metric("🏆 Best ATS Score", f"{best}%" if best else "N/A")
    st.markdown("---")

    t1,t2,t3,t4 = st.tabs(["🔍 Saved Searches","📄 Resumes","🎤 Interviews","⚙️ Profile"])

    with t1:
        st.markdown("### 🔍 Saved Job Searches")
        if not searches: st.info("No saved searches yet. Run a job search — results auto-save.")
        for s in searches:
            with st.expander(f"🔎 **{s['search_role']}** in {s['search_location'] or 'Any'} — {s['jobs_count']} jobs · {s['created_at'][:10]}"):
                for i,job in enumerate(s.get("results_json",[]),1):
                    q   = f"{job.get('title','')} {job.get('company','')}".replace(" ","+")
                    loc = job.get("location","").replace(" ","+")
                    url = f"https://www.linkedin.com/jobs/search/?keywords={q}&location={loc}"
                    st.markdown(
                        f"**{i}. {job.get('title')}** — {job.get('company')} ({job.get('location')}) | {job.get('salary','N/A')}"
                        f" &nbsp;<a href='{url}' target='_blank' style='background:#0077b5;color:white;padding:2px 10px;"
                        f"border-radius:4px;font-size:.78rem;text-decoration:none;'>🔗 Apply</a>",
                        unsafe_allow_html=True)
                if st.button("🗑️ Delete", key=f"ds_{s['id']}"): delete_job_search(s["id"],uid); st.rerun()

    with t2:
        st.markdown("### 📄 Resume Versions")
        if not resumes: st.info("No resumes yet. Optimize a resume and it appears here.")
        for r in resumes:
            clr = "#27ae60" if r["ats_score_after"]>=70 else "#f39c12" if r["ats_score_after"]>=50 else "#e74c3c"
            with st.expander(f"📄 **{r['version_name']}** · {r['target_role'] or 'N/A'} · ATS {r['ats_score_after']}% · {r['created_at'][:10]}"):
                ca,cb = st.columns(2)
                with ca:
                    st.markdown(f"**Target:** {r['target_role'] or 'N/A'}")
                    st.markdown(f"**ATS:** <span style='color:{clr};font-weight:bold'>{r['ats_score_after']}%</span> (was {r['ats_score_before']}%)", unsafe_allow_html=True)
                with cb:
                    st.markdown(f"**Matched:** {len(r.get('matched_keywords',[]))} · **Missing:** {len(r.get('missing_keywords',[]))}")
                if r.get("matched_keywords"):
                    st.markdown(" ".join(f'<span class="kw-match">{k}</span>' for k in r["matched_keywords"][:15]), unsafe_allow_html=True)
                if st.checkbox("👁️ View resume text", key=f"vr_{r['id']}"):
                    st.text_area("", value=r["optimized_resume"], height=220, key=f"ta_{r['id']}")
                docx_p = os.path.join(ROOT,"outputs",r.get("docx_filename",""))
                if r.get("docx_filename") and os.path.exists(docx_p):
                    with open(docx_p,"rb") as f:
                        st.download_button("⬇️ Download DOCX", f.read(), file_name=r["docx_filename"],
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key=f"dl_{r['id']}")
                if st.button("🗑️ Delete", key=f"dr_{r['id']}"): delete_resume_version(r["id"],uid); st.rerun()

    with t3:
        st.markdown("### 🎤 Interview Sessions")
        if not interviews: st.info("No sessions yet. Run interview prep to save Q&A here.")
        for s in interviews:
            with st.expander(f"🎤 **{s['session_name']}** · {s['domain']} · {s['total_questions']} Qs · {s['created_at'][:10]}"):
                q_data = s.get("questions_json",{})
                for i,qa in enumerate(q_data.get("technical_questions",[]),1):
                    st.markdown(f"**🔧 Q{i}: {qa.get('question','')}**")
                    st.markdown(qa.get("answer",""))
                    st.divider()
                for i,qa in enumerate(q_data.get("behavioral_questions",[]),1):
                    st.markdown(f"**🧠 B{i}: {qa.get('question','')}**")
                    st.markdown(qa.get("answer",""))
                    st.divider()

                # Re-download PDF from saved session
                st.markdown("---")
                pdf_key = f"saved_iv_pdf_{s['id']}"
                if pdf_key not in st.session_state:
                    if st.button("📄 Generate PDF", key=f"gen_pdf_{s['id']}"):
                        with st.spinner("Building PDF..."):
                            st.session_state[pdf_key] = generate_interview_pdf(
                                s["questions_json"], s["target_role"])
                        st.rerun()
                if pdf_key in st.session_state:
                    st.download_button("⬇️ Download Interview PDF", st.session_state[pdf_key],
                        file_name=f"Interview_{s['target_role'].replace(' ','_')}.pdf",
                        mime="application/pdf", key=f"dl_pdf_{s['id']}")

                if st.button("🗑️ Delete", key=f"di_{s['id']}"): delete_interview_session(s["id"],uid); st.rerun()

    with t4:
        st.markdown("### ⚙️ Edit Profile")
        st.info("This info is pre-filled in your generated resumes.")
        with st.form("profile_form"):
            ca,cb = st.columns(2)
            with ca:
                fn  = st.text_input("Full Name", value=user.get("full_name",""))
                ph  = st.text_input("Phone",     value=user.get("phone",""))
                loc = st.text_input("Location",  value=user.get("location",""))
            with cb:
                li  = st.text_input("LinkedIn URL", value=user.get("linkedin_url",""))
                gh  = st.text_input("GitHub URL",   value=user.get("github_url",""))
            st.caption(f"Username: **{user['username']}** · Email: **{user['email']}** (cannot be changed)")
            if st.form_submit_button("💾 Save Profile", type="primary"):
                update_user_profile(uid,fn,ph,loc,li,gh)
                st.session_state["full_name"] = fn
                st.success("✅ Profile updated!"); st.rerun()


# ════════════════════════════════════════════
# ADMIN PAGE
# ════════════════════════════════════════════
def show_admin():
    if not is_admin(): st.error("🚫 Admin access required."); return
    admin_uname = st.session_state.get("username","admin")
    st.markdown('<div class="admin-banner"><h2>🛡️ Admin Dashboard</h2><p>User management and system oversight</p></div>', unsafe_allow_html=True)

    stats = get_admin_stats()
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("👥 Users",      stats["total_users"])
    c2.metric("🆕 This Week",  stats["new_users_week"])
    c3.metric("🔍 Searches",   stats["total_searches"])
    c4.metric("📄 Resumes",    stats["total_resumes"])
    c5.metric("🎤 Interviews", stats["total_interviews"])
    st.markdown("---")

    t1,t2,t3 = st.tabs(["👥 Users","📊 Activity","📈 Insights"])
    with t1:
        st.markdown("### All Users")
        users = get_all_users()
        q = st.text_input("🔎 Filter", placeholder="Search username or email")
        if q: users = [u for u in users if q.lower() in u["username"] or q.lower() in u["email"]]
        for u in users:
            icon  = "🟢" if u["is_active"] else "🔴"
            badge = "🛡️ ADMIN" if u["role"]=="admin" else "👤 USER"
            with st.expander(f"{icon} **{u['username']}** ({u['email']}) · {badge} · {u['created_at'][:10]}"):
                ca,cb,cc = st.columns(3)
                with ca: st.markdown(f"**Name:** {u.get('full_name') or 'N/A'}")
                with cb:
                    st.markdown(f"**Status:** {'✅ Active' if u['is_active'] else '🚫 Inactive'}")
                    st.markdown(f"**Last Login:** {(u.get('last_login') or 'Never')[:16]}")
                with cc:
                    if u["username"] != admin_uname:
                        label = "🚫 Deactivate" if u["is_active"] else "✅ Activate"
                        if st.button(label, key=f"tog_{u['id']}"):
                            toggle_user_active(u["id"], not u["is_active"])
                            log_activity(st.session_state["user_id"], admin_uname, "admin_toggle", u["username"])
                            st.rerun()
                    else: st.caption("*(Your account)*")
    with t2:
        st.markdown("### Recent Activity")
        acts = get_recent_activity(100)
        if not acts: st.info("No activity yet.")
        icons = {"login":"🔑","logout":"🚪","register":"✨","search":"🔍",
                 "resume_saved":"📄","interview_saved":"🎤","admin_toggle":"⚙️"}
        for a in acts:
            ic = icons.get(a["action"],"📌")
            st.markdown(f"{ic} `{a['created_at'][:16]}` — **{a['username'] or 'system'}** → `{a['action']}`"
                        +(f" · {a['details']}" if a.get("details") else ""))
    with t3:
        st.markdown("### Insights")
        top = stats.get("top_roles",[])
        if top:
            st.markdown("#### Most Searched Roles")
            mx = max(r["cnt"] for r in top)
            for i,r in enumerate(top,1):
                pct = int(r["cnt"]/mx*100)
                st.markdown(f"""<div style="margin-bottom:.5rem;">
                    <b>#{i} {r['search_role']}</b>
                    <span style="float:right;color:#666">{r['cnt']} searches</span>
                    <div style="background:#eee;border-radius:4px;height:8px;margin-top:3px;">
                        <div style="background:#2e74b5;width:{pct}%;height:8px;border-radius:4px;"></div>
                    </div></div>""", unsafe_allow_html=True)
        else: st.info("No search data yet.")


# ════════════════════════════════════════════
# JOB CARD
# ════════════════════════════════════════════
def show_job_card(job: dict, idx: int):
    title   = job.get("title","")
    company = job.get("company","")
    loc     = job.get("location","")
    salary  = job.get("salary","N/A")
    exp     = job.get("experience_required","")
    skills  = job.get("skills_required",[])
    score   = job.get("relevance_score",0)
    q       = f"{title} {company}".replace(" ","+")
    ql      = loc.replace(" ","+")
    li      = f"https://www.linkedin.com/jobs/search/?keywords={q}&location={ql}"
    nk      = f"https://www.naukri.com/{title.lower().replace(' ','-')}-jobs-in-{loc.lower().replace(' ','-')}"
    ind     = f"https://in.indeed.com/jobs?q={q}&l={ql}"

    with st.expander(f"#{idx}  **{title}** — {company} | 📍 {loc} | 💰 {salary}", expanded=(idx==1)):
        ca,cb = st.columns([2,1])
        with ca:
            st.markdown(f"**🏢 Company:** {company}  |  **📍 Location:** {loc}")
            st.markdown(f"**📅 Experience:** {exp} yrs  |  **⭐ Match:** {'⭐'*min(score,5)}")
            st.markdown(job.get("description",""))
        with cb:
            st.markdown(f"**💰 Salary:** {salary}")
        if skills:
            st.markdown("**🔧 Required Skills:**")
            st.markdown(" ".join(f'<span class="kw-match">{s}</span>' for s in skills), unsafe_allow_html=True)
        st.markdown("**🔗 Apply on:**")
        c1,c2,c3 = st.columns(3)
        with c1: st.markdown(f'<a href="{li}" target="_blank" style="display:inline-block;background:#0077b5;color:white;padding:7px 16px;border-radius:6px;text-decoration:none;font-weight:bold;">💼 LinkedIn</a>', unsafe_allow_html=True)
        with c2: st.markdown(f'<a href="{nk}" target="_blank" style="display:inline-block;background:#ff7555;color:white;padding:7px 16px;border-radius:6px;text-decoration:none;font-weight:bold;">🇮🇳 Naukri</a>', unsafe_allow_html=True)
        with c3: st.markdown(f'<a href="{ind}" target="_blank" style="display:inline-block;background:#2164f3;color:white;padding:7px 16px;border-radius:6px;text-decoration:none;font-weight:bold;">🌐 Indeed</a>', unsafe_allow_html=True)


# ════════════════════════════════════════════
# ATS KEYWORDS SECTION
# ════════════════════════════════════════════
def show_ats_keywords_section(ats_data: dict, role: str):
    st.markdown("---")
    st.markdown(f"### 🎯 ATS Keywords for **{role}** — Use These in Your Resume")
    st.caption(f"Extracted from {ats_data.get('total_jobs_analyzed',0)} job listings · Add these to boost your ATS score")

    c1,c2 = st.columns(2)
    with c1:
        if ats_data.get("must_have"):
            st.markdown("#### 🔴 Must-Have Keywords")
            st.caption("These appear in most job listings — critical to include")
            st.markdown(" ".join(f'<span class="kw-hot">{k}</span>' for k in ats_data["must_have"]), unsafe_allow_html=True)

        if ats_data.get("tools"):
            st.markdown("#### 🔧 Tools & Technologies")
            st.caption("Specific tools mentioned in job descriptions")
            st.markdown(" ".join(f'<span class="kw-ats">{k}</span>' for k in ats_data["tools"]), unsafe_allow_html=True)

    with c2:
        if ats_data.get("good_to_have"):
            st.markdown("#### 🟡 Good to Have")
            st.caption("Secondary keywords that improve your ranking")
            st.markdown(" ".join(f'<span class="kw-match">{k}</span>' for k in ats_data["good_to_have"]), unsafe_allow_html=True)

        if ats_data.get("soft_skills"):
            st.markdown("#### 🤝 Soft Skills")
            st.caption("Behavioral keywords ATS systems look for")
            st.markdown(" ".join(f'<span class="kw-ats">{k}</span>' for k in ats_data["soft_skills"]), unsafe_allow_html=True)

    st.info("💡 **How to use this:** Copy the Must-Have keywords and weave them into your resume's Skills section, bullet points, and Summary. Then paste the Job Description + your resume into the **Resume Optimizer** tab to see your ATS score improve.")


# ════════════════════════════════════════════
# ROUTING
# ════════════════════════════════════════════
if not is_authenticated():
    show_login_page()
    st.stop()

username  = get_current_username()
user_id   = st.session_state.get("user_id")
user_data = st.session_state.get("user_data", {})

# ── Sidebar ──
with st.sidebar:
    st.markdown(f"""
    <div style="background:#1e3a5f;color:white;padding:.8rem 1rem;border-radius:8px;margin-bottom:1rem;">
        <div style="font-size:.75rem;color:#aac8e4;">Logged in as</div>
        <div style="font-weight:bold;font-size:1rem;">👤 {st.session_state.get('full_name') or username}</div>
        <div style="font-size:.72rem;color:#aac8e4;">@{username} · {st.session_state.get('role','user').upper()}</div>
    </div>""", unsafe_allow_html=True)

    pages = ["🚀 Job Search","📊 My Dashboard"]
    if is_admin(): pages.append("🛡️ Admin Panel")
    page = st.selectbox("Navigate to", pages, label_visibility="collapsed")

    # if not is_admin():
    #     st.markdown("""
    #     <div style="background:#fff8e1;border:1px solid #f0c040;border-radius:6px;
    #                 padding:.5rem .7rem;font-size:.78rem;color:#7a5c00;">
    #         🛡️ Want Admin Panel?<br>
    #         Run: <code>python make_admin.py your_username</code><br>then restart &amp; re-login.
        # </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Safe defaults — always declared regardless of page
    role=location=job_description=resume_text=run_mode=""
    auto_save=True; run_button=False; experience=2

    if page == "🚀 Job Search":
        if not GROQ_API_KEY: st.error("⚠️ GROQ_API_KEY missing in .env")
        st.markdown("### 🎯 Job Preferences")
        role       = st.text_input("Job Role *", placeholder="e.g. Data Scientist")
        location   = st.text_input("Location",   placeholder="e.g. Bangalore, Remote")
        experience = st.slider("Years of Experience", 0, 15, 2)
        st.markdown("---")
        st.markdown("### 📄 Your Resume")
        mode = st.radio("Input:", ["📋 Paste text","📂 Upload (.txt/.docx)"])
        if mode == "📋 Paste text":
            resume_text = st.text_area("Paste resume", height=150, placeholder="Paste your full resume here...")
        else:
            uf = st.file_uploader("Upload file", type=["txt","docx"])
            if uf:
                try:
                    resume_text = parse_resume_from_upload(uf)
                    st.success(f"✅ Loaded ({len(resume_text)} chars)")
                except Exception as e: st.error(str(e))
        st.markdown("---")
        st.markdown("### 📋 Job Description")
        job_description = st.text_area("Paste JD (optional)", height=120,
                                        placeholder="Paste the target job description for tailored resume + interview prep...")
        st.markdown("---")
        st.markdown("### 🔧 Mode")
        run_mode = st.selectbox("What to run:", [
            "🚀 Full Pipeline (All Agents)",
            "🔍 Job Search Only",
            "📝 Resume Optimization Only",
            "🎤 Interview Prep Only"
        ])
        auto_save  = st.checkbox("💾 Auto-save to dashboard", value=True)
        run_button = st.button("▶️ Run AI Pipeline", type="primary", use_container_width=True)

    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        # Clear all cached results on logout
        for k in list(st.session_state.keys()):
            if k not in ["authenticated","user_id","username","full_name","email","role","user_data"]:
                del st.session_state[k]
        logout_user(); st.rerun()

# ── Route ──
if page == "📊 My Dashboard": show_dashboard(); st.stop()
if page == "🛡️ Admin Panel":  show_admin();     st.stop()


# ════════════════════════════════════════════
# JOB SEARCH PAGE
# ════════════════════════════════════════════
st.markdown("""
<div class="banner">
    <h1>🤖 Multi-Agent AI For Job Seeker</h1>
    <p>Find jobs · Optimize your resume · Ace your interviews — powered by Groq LLaMA 3.1</p>
</div>""", unsafe_allow_html=True)

if not GROQ_API_KEY:
    st.error("⚠️ **Groq API key not found.** Create `.env` with `GROQ_API_KEY=your_key`.")
    st.stop()

if not run_button and "last_results" not in st.session_state:
    c1,c2,c3 = st.columns(3)
    c1.markdown("### 🔍 Job Discovery\nFinds and ranks matching jobs. Each result has **LinkedIn, Naukri & Indeed** apply links plus ATS keywords to improve your resume.")
    c2.markdown("### 📝 Resume Optimizer\nTailors resume to the JD. Shows ATS score before & after. Download as **DOCX**")
    c3.markdown("### 🎤 Interview Prep\nJD-specific technical, behavioral & system design Q&A with detailed answers. Download as **professional PDF**.")
    st.info("👈 Fill in your preferences in the sidebar and click **Run AI Pipeline**.")
    st.stop()

if not role.strip() and run_button:
    st.error("⚠️ Please enter a Job Role in the sidebar."); st.stop()

# ── Run pipeline if button clicked ──
if run_button and role.strip():
    user_info = {
        "name":     user_data.get("full_name") or st.session_state.get("full_name",""),
        "email":    user_data.get("email",""),
        "phone":    user_data.get("phone",""),
        "location": user_data.get("location",""),
        "linkedin": user_data.get("linkedin_url",""),
        "github":   user_data.get("github_url","")
    }
    from orchestrator.crew_orchestrator import JobSeekerOrchestrator
    with st.spinner("🤖 AI agents working... (~30-60 seconds)"):
        try:
            orch = JobSeekerOrchestrator()
            if "Job Search Only" in run_mode:
                raw = orch.run_job_search_only(role, location, experience)
                results = {"job_discovery":raw,"job_profile":None,"resume":None,"interview":None,"errors":[]}
            elif "Resume Optimization Only" in run_mode:
                if not resume_text.strip() or not job_description.strip():
                    st.error("⚠️ Provide both resume and job description."); st.stop()
                raw = orch.run_resume_only(resume_text, job_description, user_info)
                results = {"job_discovery":None,"job_profile":None,"resume":raw,"interview":None,"errors":[]}
            elif "Interview Prep Only" in run_mode:
                if not job_description.strip():
                    st.error("⚠️ Provide a job description."); st.stop()
                raw = orch.run_interview_only(job_description, experience)
                results = {"job_discovery":None,"job_profile":None,"resume":None,"interview":raw,"errors":[]}
            else:
                results = orch.run_full_pipeline(
                    role=role, location=location, experience=experience,
                    resume_text=resume_text, job_description=job_description,
                    user_info=user_info)
        except Exception as e:
            st.error(f"❌ Pipeline error: {str(e)}"); st.exception(e); st.stop()

    # ── Store results in session_state so they survive any button click ──
    st.session_state["last_results"]  = results
    st.session_state["last_role"]     = role
    st.session_state["last_location"] = location

    # ── Pre-generate PDFs NOW and store bytes in session_state ──
    # This means download buttons are always ready — no generate-then-click loop
    if results.get("interview"):
        with st.spinner("📄 Pre-generating interview PDF..."):
            try:
                st.session_state["iv_pdf_bytes"] = generate_interview_pdf(results["interview"], role)
                st.session_state["iv_pdf_name"]  = f"Interview_Prep_{role.replace(' ','_')}.pdf"
            except Exception as e:
                st.warning(f"PDF generation failed: {e}")

    if results.get("resume"):
        docx_path = results["resume"].get("docx_path","")
        if docx_path and os.path.exists(docx_path):
            with open(docx_path,"rb") as f:
                st.session_state["resume_docx_bytes"] = f.read()
                st.session_state["resume_docx_name"]  = os.path.basename(docx_path)

    # ── ATS keywords from job results ──
    if results.get("job_discovery") and results["job_discovery"].get("jobs"):
        jobs = results["job_discovery"]["jobs"]
        st.session_state["ats_keywords"] = generate_ats_keywords_for_role(role, jobs)
    else:
        st.session_state.pop("ats_keywords", None)

    # ── Auto-save ──
    if auto_save and user_id:
        try:
            if results.get("job_discovery") and results["job_discovery"].get("jobs"):
                save_job_search(user_id, role, location, experience, results["job_discovery"]["jobs"])
                log_activity(user_id, username, "search", f"{role} in {location}")
            if results.get("resume") and resume_text:
                r = results["resume"]
                dfn = os.path.basename(r.get("docx_path","")) if r.get("docx_path") else ""
                save_resume_version(user_id, f"{role} Resume", resume_text,
                    r.get("optimized_resume_text",""), job_description, role,
                    r.get("original_score",0), r.get("optimized_score",0),
                    r.get("matched_keywords",[]), r.get("missing_keywords",[]), dfn)
                log_activity(user_id, username, "resume_saved", role)
            if results.get("interview"):
                iv = results["interview"]
                save_interview_session(user_id, f"{role} Interview Prep", role,
                    iv.get("domain",""), iv.get("seniority",""), iv)
                log_activity(user_id, username, "interview_saved", role)
            st.success("💾 Results saved to Dashboard!", icon="✅")
        except Exception as e:
            st.warning(f"⚠️ Could not save: {e}")

# ── Load results from session_state (survives any button click) ──
if "last_results" not in st.session_state: st.stop()
results = st.session_state["last_results"]
role    = st.session_state.get("last_role", role)

if results.get("errors"):
    with st.expander(f"⚠️ {len(results['errors'])} warning(s)"):
        for e in results["errors"]: st.warning(e)

# ── Build tabs ──
tab_labels = []
if results.get("job_discovery"): tab_labels.append("🔍 Jobs Found")
if results.get("resume"):        tab_labels.append("📝 Optimized Resume")
if results.get("interview"):     tab_labels.append("🎤 Interview Prep")
if results.get("job_profile"):   tab_labels.append("🔬 Job Profile")
if not tab_labels: st.error("No results. Check inputs and try again."); st.stop()

tabs = st.tabs(tab_labels)
ti = 0

# ── Jobs Tab ──
if results.get("job_discovery"):
    with tabs[ti]:
        jd = results["job_discovery"]
        st.markdown(f"### 📊 {jd.get('count',0)} Jobs Found for **{role}**")
        if jd.get("summary"): st.info(jd["summary"])
        jobs = jd.get("jobs",[])
        if jobs:
            for i,job in enumerate(jobs,1): show_job_card(job,i)
            # ATS Keywords section below job cards
            if st.session_state.get("ats_keywords"):
                show_ats_keywords_section(st.session_state["ats_keywords"], role)
        else:
            st.warning("No jobs found. Try a broader role (e.g. 'Data Scientist' not 'Data Science').")
    ti += 1

# ── Resume Tab ──
if results.get("resume"):
    with tabs[ti]:
        r = results["resume"]
        st.markdown("### 📊 ATS Compatibility Score")
        c1,c2,c3 = st.columns(3)
        orig,new  = r.get("original_score",0), r.get("optimized_score",0)
        imp = new - orig
        with c1:
            cls = "score-high" if orig>=70 else "score-mid" if orig>=50 else "score-low"
            st.markdown("**Before**")
            st.markdown(f'<span class="{cls}">{orig}%</span>', unsafe_allow_html=True)
        with c2:
            cls = "score-high" if new>=70 else "score-mid" if new>=50 else "score-low"
            st.markdown("**After**")
            st.markdown(f'<span class="{cls}">{new}%</span>', unsafe_allow_html=True)
        with c3:
            color = "#27ae60" if imp>=0 else "#e74c3c"
            st.markdown("**Improvement**")
            st.markdown(f'<span style="color:{color};font-weight:bold;font-size:1.4rem;">+{imp}%</span>', unsafe_allow_html=True)
        st.markdown("---")
        cm,cmiss = st.columns(2)
        with cm:
            if r.get("matched_keywords"):
                st.markdown(f"**✅ Matched ({len(r['matched_keywords'])})**")
                st.markdown(" ".join(f'<span class="kw-match">{k}</span>' for k in r["matched_keywords"][:20]), unsafe_allow_html=True)
        with cmiss:
            if r.get("missing_keywords"):
                st.markdown(f"**❌ Missing ({len(r['missing_keywords'])})**")
                st.markdown(" ".join(f'<span class="kw-miss">{k}</span>' for k in r["missing_keywords"][:20]), unsafe_allow_html=True)
        st.markdown("---")
        for s in r.get("suggestions",[]): st.markdown(f"- {s}")
        st.text_area("Optimized Resume Text (copy this)", value=r.get("optimized_resume_text",""), height=350)

        # ── DOCX download — always ready from session_state, never refreshes ──
        if st.session_state.get("resume_docx_bytes"):
            st.download_button(
                "⬇️ Download ATS Resume (.docx)",
                data      = st.session_state["resume_docx_bytes"],
                file_name = st.session_state.get("resume_docx_name","ATS_Resume.docx"),
                mime      = "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type      = "primary"
            )
    ti += 1

# ── Interview Tab ──
if results.get("interview"):
    with tabs[ti]:
        iv = results["interview"]
        st.markdown(f"### 🎤 Interview Prep — {iv.get('domain', role)}")
        st.caption(f"Seniority: **{iv.get('seniority','mid-level').title()}**")

        if iv.get("key_talking_points"):
            st.markdown("### 💬 Key Talking Points")
            for tp in iv["key_talking_points"]: st.markdown(f"✦ {tp}")
            st.markdown("---")

        tech = iv.get("technical_questions",[])
        if tech:
            st.markdown(f"### 🔧 Technical Questions ({len(tech)})")
            for i,qa in enumerate(tech,1):
                with st.expander(f"Q{i}: {qa.get('question','')}", expanded=(i==1)):
                    st.markdown(f"**📌 Answer:**\n\n{qa.get('answer','')}")
                    if qa.get("follow_up"):
                        st.markdown(f"**🔁 Follow-up:** *{qa['follow_up']}*")
                    if qa.get("tip"): st.info(f"💡 {qa['tip']}")

        beh = iv.get("behavioral_questions",[])
        if beh:
            st.markdown(f"### 🧠 Behavioral Questions ({len(beh)})")
            for i,qa in enumerate(beh,1):
                with st.expander(f"B{i}: {qa.get('question','')}"):
                    st.markdown(f"**📌 STAR Answer:**\n\n{qa.get('answer','')}")
                    if qa.get("tip"): st.info(f"💡 {qa['tip']}")

        sd = iv.get("system_design_questions",[])
        if sd:
            st.markdown(f"### 🏗️ System Design ({len(sd)})")
            for i,qa in enumerate(sd,1):
                with st.expander(f"SD{i}: {qa.get('question','')}"):
                    approach = qa.get("approach",[])
                    for step in (approach if isinstance(approach,list) else [approach]):
                        st.markdown(f"→ {step}")
                    if qa.get("key_concepts"):
                        st.info(f"🎯 Testing: {qa['key_concepts']}")

        if iv.get("preparation_tips"):
            st.markdown("### 📚 Preparation Tips")
            for tip in iv["preparation_tips"]: st.markdown(f"• {tip}")

        # ── PDF Download — pre-generated, always ready ──
        st.markdown("---")
        if st.session_state.get("iv_pdf_bytes"):
            st.success("✅ PDF ready!")
            st.download_button(
                "⬇️ Download Interview Prep PDF",
                data      = st.session_state["iv_pdf_bytes"],
                file_name = st.session_state.get("iv_pdf_name","Interview_Prep.pdf"),
                mime      = "application/pdf",
                type      = "primary"
            )
        else:
            st.warning("PDF not available. Re-run the pipeline to generate it.")
    ti += 1

# ── Job Profile Tab ──
if results.get("job_profile"):
    with tabs[ti]:
        p = results["job_profile"]
        st.markdown("### 🔬 Job Profile Analysis")
        st.markdown(f"**Domain:** {p.get('domain')} · **Seniority:** {p.get('seniority','').title()}")
        if p.get("profile_summary"): st.info(p["profile_summary"])
        ca,cb = st.columns(2)
        with ca:
            st.markdown("**Skills:**")
            for s in p.get("skills",[]): st.markdown(f"• {s}")
        with cb:
            st.markdown("**Responsibilities:**")
            for r in p.get("responsibilities",[]): st.markdown(f"• {r}")
        if p.get("keywords"):
            st.markdown(" ".join(f'<span class="kw-match">{k}</span>' for k in p["keywords"]), unsafe_allow_html=True)

elapsed = results.get("elapsed_seconds",0)
st.markdown("---")
st.caption(f"⚡ Completed in {elapsed}s · 🤖 Groq LLaMA 3.1 · 👤 @{username}")
