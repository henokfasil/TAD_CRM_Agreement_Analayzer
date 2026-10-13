from __future__ import annotations

from html import escape

import streamlit as st


def apply_app_style() -> None:
    st.markdown(
        """
        <style>
        :root { --crm-navy:#12344d; --crm-blue:#176b87; --crm-teal:#159895; --crm-ink:#173042; --crm-muted:#607789; --crm-border:#dbe5eb; }
        .stApp { background:#f5f8fa; color:var(--crm-ink); }
        .main .block-container { max-width:1440px; padding-top:2rem; padding-bottom:4rem; }
        [data-testid="stSidebar"] { background:linear-gradient(180deg,#edf5f7 0%,#f8fafb 68%,#eef3f6 100%); border-right:1px solid var(--crm-border); }
        [data-testid="stSidebarNav"] { padding-top:.45rem; }
        [data-testid="stSidebarNav"]::before { content:"CRM INTELLIGENCE"; display:block; color:var(--crm-navy); font-size:.82rem; font-weight:800; letter-spacing:.10em; padding:.55rem 1.35rem .8rem; }
        [data-testid="stSidebarNav"] ul { gap:.05rem; }
        [data-testid="stSidebarNav"] li a { padding-top:.34rem; padding-bottom:.34rem; }
        [data-testid="stSidebarNav"] span { font-weight:560; }
        [data-testid="stSidebarNav"] a[aria-current="page"] { background:#dceef1; color:var(--crm-navy); border-left:4px solid var(--crm-teal); border-radius:0 10px 10px 0; }
        .crm-brand { margin:.25rem 0 1rem; padding:1rem; border-radius:14px; color:white; background:linear-gradient(135deg,var(--crm-navy),var(--crm-blue)); box-shadow:0 8px 20px rgba(18,52,77,.14); }
        .crm-brand strong { display:block; font-size:1.05rem; letter-spacing:.01em; }
        .crm-brand span { color:#cde9ee; font-size:.78rem; }
        .crm-header { margin:0 0 1.5rem; }
        .crm-eyebrow { color:var(--crm-teal); font-size:.76rem; font-weight:750; letter-spacing:.12em; text-transform:uppercase; margin-bottom:.35rem; }
        .crm-header h1 { color:var(--crm-navy); font-size:clamp(2rem,4vw,3.15rem); letter-spacing:-.035em; line-height:1.05; margin:0; }
        .crm-header p { color:var(--crm-muted); font-size:1.03rem; line-height:1.65; max-width:820px; margin:.65rem 0 0; }
        .crm-hero { padding:clamp(1.5rem,4vw,3rem); border:1px solid #cde0e8; border-radius:24px; background:radial-gradient(circle at 92% 10%,rgba(21,152,149,.20),transparent 28%),linear-gradient(135deg,#fff 0%,#eef7f8 100%); box-shadow:0 16px 38px rgba(18,52,77,.09); margin-bottom:1.4rem; }
        .crm-hero h1 { color:var(--crm-navy); font-size:clamp(2.35rem,5vw,4.2rem); line-height:1.03; letter-spacing:-.04em; margin:.3rem 0 0; }
        .crm-hero p { color:var(--crm-muted); max-width:780px; font-size:1.08rem; line-height:1.7; }
        .crm-kicker { color:var(--crm-teal); font-weight:750; letter-spacing:.12em; text-transform:uppercase; font-size:.78rem; }
        [data-testid="stMetric"] { background:#fff; border:1px solid var(--crm-border); border-radius:14px; padding:1rem 1.05rem; box-shadow:0 5px 16px rgba(18,52,77,.045); }
        [data-testid="stMetricLabel"] { color:var(--crm-muted); }
        [data-testid="stMetricValue"] { color:var(--crm-navy); font-weight:720; }
        [data-testid="stTabs"] [role="tablist"] { gap:.35rem; }
        [data-testid="stTabs"] button[role="tab"] { border-radius:10px 10px 0 0; padding:.65rem 1rem; }
        [data-testid="stTabs"] button[aria-selected="true"] { color:var(--crm-blue); font-weight:700; }
        div.stButton > button, div.stDownloadButton > button { border-radius:10px; border-color:#b9ccd6; min-height:2.65rem; font-weight:650; }
        div.stButton > button[kind="primary"] { background:linear-gradient(135deg,var(--crm-blue),var(--crm-teal)); border:0; color:#fff; box-shadow:0 7px 16px rgba(21,152,149,.20); }
        [data-testid="stFileUploaderDropzone"] { background:#f9fcfd; border:1.5px dashed #87b8c4; border-radius:16px; }
        [data-testid="stAlert"] { border-radius:12px; }
        [data-testid="stDataFrame"] { border:1px solid var(--crm-border); border-radius:12px; overflow:hidden; }
        hr { border-color:var(--crm-border); }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, description: str, *, eyebrow: str = "Research workspace") -> None:
    st.markdown(
        f'<div class="crm-header"><div class="crm-eyebrow">{escape(eyebrow)}</div><h1>{escape(title)}</h1><p>{escape(description)}</p></div>',
        unsafe_allow_html=True,
    )
