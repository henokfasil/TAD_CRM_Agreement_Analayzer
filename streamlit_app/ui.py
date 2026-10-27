from __future__ import annotations

from html import escape

import streamlit as st


def apply_app_style() -> None:
    st.markdown(
        """
        <style>
        :root { --crm-forest:#314b3d; --crm-sage:#627d68; --crm-clay:#b9684a; --crm-ochre:#d0a251; --crm-ink:#303a32; --crm-muted:#6f766e; --crm-paper:#fffdf8; --crm-canvas:#f7f2ea; --crm-border:#ded3c4; }
        .stApp { background:var(--crm-canvas); color:var(--crm-ink); }
        .main .block-container { max-width:1320px; padding-top:2.4rem; padding-bottom:5rem; }
        p, label, [data-testid="stMarkdownContainer"] { line-height:1.62; }
        h1, h2, h3, h4 { color:var(--crm-forest); }
        [data-testid="stSidebar"] { background:linear-gradient(180deg,#ede4d7 0%,#f5eee4 52%,#ebe1d3 100%); border-right:1px solid #d7c9b8; min-width:245px; }
        [data-testid="stSidebarNav"] { padding-top:.45rem; }
        [data-testid="stSidebarNav"]::before { content:"CRM  ·  AGREEMENT STUDIO"; display:block; color:var(--crm-forest); font-family:Georgia,serif; font-size:.87rem; font-weight:700; letter-spacing:.08em; padding:.7rem 1.35rem 1rem; }
        [data-testid="stSidebarNav"] ul { gap:.05rem; }
        [data-testid="stSidebarNav"] li a { padding-top:.43rem; padding-bottom:.43rem; font-size:.91rem; }
        [data-testid="stSidebarNav"] span { font-weight:580; }
        [data-testid="stSidebarNav"] a[aria-current="page"] { background:#ddcdbd; color:var(--crm-forest); border-left:4px solid var(--crm-clay); border-radius:0 12px 12px 0; }
        .crm-header { margin:0 0 1.5rem; }
        .crm-eyebrow { color:var(--crm-clay); font-size:.76rem; font-weight:750; letter-spacing:.12em; text-transform:uppercase; margin-bottom:.45rem; }
        .crm-header h1 { color:var(--crm-forest); font-family:Georgia,serif; font-size:clamp(2rem,4vw,3.15rem); font-weight:600; letter-spacing:-.025em; line-height:1.08; margin:0; }
        .crm-header p { color:var(--crm-muted); font-size:1.03rem; line-height:1.65; max-width:820px; margin:.65rem 0 0; }
        .crm-hero { display:grid; grid-template-columns:minmax(0,1.45fr) minmax(250px,.55fr); gap:2rem; align-items:center; padding:clamp(2rem,5vw,4.2rem); border:1px solid #ddcfbf; border-radius:30px; background:linear-gradient(135deg,#fffdf8 0%,#f2e8db 100%); box-shadow:0 22px 55px rgba(74,57,39,.10); margin-bottom:1.6rem; overflow:hidden; }
        .crm-hero h1 { color:var(--crm-forest); font-family:Georgia,serif; font-size:clamp(2.5rem,5vw,4.65rem); font-weight:500; line-height:1.02; letter-spacing:-.035em; margin:.45rem 0 1rem; }
        .crm-hero p { color:var(--crm-muted); max-width:720px; font-size:1.08rem; line-height:1.75; }
        .crm-kicker { color:var(--crm-clay); font-weight:750; letter-spacing:.13em; text-transform:uppercase; font-size:.76rem; }
        .crm-paper-stack { position:relative; height:240px; }
        .crm-paper { position:absolute; width:78%; height:185px; right:6%; top:25px; padding:1.5rem; border-radius:8px; background:var(--crm-paper); border:1px solid #d8cbbb; box-shadow:0 15px 30px rgba(76,58,39,.14); transform:rotate(4deg); }
        .crm-paper::before { content:"ARTICLE 4"; color:var(--crm-clay); font-size:.7rem; font-weight:800; letter-spacing:.12em; }
        .crm-paper::after { content:"Evidence  →  classification  →  review"; display:block; margin-top:1.3rem; color:var(--crm-forest); font-family:Georgia,serif; font-size:1.2rem; line-height:1.45; }
        .crm-paper-back { position:absolute; width:74%; height:178px; right:19%; top:8px; border-radius:8px; background:#d9c5aa; transform:rotate(-5deg); }
        [data-testid="stMetric"] { background:var(--crm-paper); border:1px solid var(--crm-border); border-radius:18px; padding:1.05rem 1.15rem; box-shadow:0 8px 22px rgba(74,57,39,.055); }
        [data-testid="stMetricLabel"] { color:var(--crm-muted); }
        [data-testid="stMetricValue"] { color:var(--crm-forest); font-family:Georgia,serif; font-weight:650; }
        [data-testid="stTabs"] [role="tablist"] { gap:.35rem; }
        [data-testid="stTabs"] button[role="tab"] { border-radius:10px 10px 0 0; padding:.65rem 1rem; }
        [data-testid="stTabs"] button[aria-selected="true"] { color:var(--crm-clay); font-weight:700; }
        div.stButton > button, div.stDownloadButton > button { border-radius:13px; border-color:#c9b9a6; min-height:2.8rem; font-weight:650; }
        div.stButton > button[kind="primary"] { background:linear-gradient(135deg,var(--crm-forest),var(--crm-sage)); border:0; color:#fff; box-shadow:0 8px 18px rgba(49,75,61,.20); }
        [data-testid="stFileUploaderDropzone"] { background:var(--crm-paper); border:1.5px dashed #b99f82; border-radius:18px; }
        [data-testid="stFileUploaderDropzone"]:hover { border-color:var(--crm-clay); background:#fffaf2; }
        [data-testid="stFileUploaderDropzone"] button { background:var(--crm-forest); color:white; border:0; }
        [data-testid="stAlert"] { border-radius:12px; }
        [data-testid="stDataFrame"] { border:1px solid var(--crm-border); border-radius:12px; overflow:hidden; }
        hr { border-color:var(--crm-border); }
        .crm-section-title { margin:2rem 0 .4rem; font-family:Georgia,serif; font-size:1.7rem; color:var(--crm-forest); }
        .crm-section-note { color:var(--crm-muted); margin-bottom:1.1rem; }
        .crm-flow { display:grid; grid-template-columns:repeat(3,1fr); gap:1rem; margin:1rem 0 1.5rem; }
        .crm-flow-card { min-height:155px; padding:1.35rem; border-radius:20px; background:var(--crm-paper); border:1px solid var(--crm-border); box-shadow:0 8px 20px rgba(74,57,39,.05); }
        .crm-flow-number { display:inline-grid; place-items:center; width:2.2rem; height:2.2rem; border-radius:50%; color:#fff; background:var(--crm-clay); font-family:Georgia,serif; font-weight:700; }
        .crm-flow-card:nth-child(2) .crm-flow-number { background:var(--crm-sage); }
        .crm-flow-card:nth-child(3) .crm-flow-number { background:var(--crm-ochre); color:#493b27; }
        .crm-flow-card h3 { margin:.9rem 0 .4rem; font-family:Georgia,serif; font-size:1.15rem; }
        .crm-flow-card p { color:var(--crm-muted); font-size:.92rem; margin:0; }
        .crm-result-panel { margin:1.35rem 0 1rem; padding:1.45rem; background:linear-gradient(135deg,#fffdf8 0%,#f4eee4 100%); border:1px solid var(--crm-border); border-radius:22px; box-shadow:0 14px 35px rgba(74,57,39,.07); }
        .crm-result-panel--warning { background:linear-gradient(135deg,#fffdf8 0%,#fbf4df 100%); border-color:#e3ca88; }
        .crm-result-panel--warning .crm-result-check { background:#a8731f; }
        .crm-result-panel--warning .crm-result-kicker { color:#8a5d18; }
        .crm-result-panel--warning .crm-status-pill { background:#f5e4b7; color:#765016; }
        .crm-result-heading { display:grid; grid-template-columns:auto minmax(0,1fr) auto; gap:.9rem; align-items:center; padding-bottom:1.15rem; border-bottom:1px solid var(--crm-border); }
        .crm-result-check { display:grid; place-items:center; width:2.45rem; height:2.45rem; border-radius:50%; background:var(--crm-forest); color:white; font-size:1.1rem; }
        .crm-result-kicker { color:var(--crm-sage); font-size:.7rem; font-weight:800; letter-spacing:.13em; text-transform:uppercase; }
        .crm-result-heading h3 { margin:.12rem 0 0; font-family:Georgia,serif; font-size:1.18rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .crm-status-pill { padding:.38rem .72rem; border-radius:999px; background:#e3ebdf; color:var(--crm-forest); font-size:.76rem; font-weight:700; }
        .crm-summary-grid { display:grid; grid-template-columns:repeat(5,minmax(110px,1fr)); gap:0; padding-top:1.15rem; }
        .crm-summary-grid > div { min-width:0; padding:.15rem 1rem; border-right:1px solid var(--crm-border); }
        .crm-summary-grid > div:first-child { padding-left:0; }
        .crm-summary-grid > div:last-child { border-right:0; }
        .crm-summary-grid span { display:block; margin-bottom:.24rem; color:var(--crm-muted); font-size:.72rem; letter-spacing:.04em; text-transform:uppercase; }
        .crm-summary-grid strong { display:block; color:var(--crm-forest); font-size:.96rem; font-weight:700; white-space:normal; overflow-wrap:anywhere; }
        .crm-preview-title { margin:1.8rem 0 .25rem; font-family:Georgia,serif; font-size:1.45rem; color:var(--crm-forest); }
        @media (max-width:800px) { .crm-hero { grid-template-columns:1fr; } .crm-paper-stack { display:none; } .crm-flow { grid-template-columns:1fr; } }
        @media (max-width:900px) { .crm-summary-grid { grid-template-columns:repeat(2,1fr); gap:.85rem; } .crm-summary-grid > div, .crm-summary-grid > div:first-child { padding:.2rem 0; border-right:0; } }
        @media (max-width:560px) { .crm-result-panel { padding:1rem; border-radius:16px; } .crm-result-heading { grid-template-columns:auto minmax(0,1fr); } .crm-status-pill { grid-column:2; justify-self:start; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, description: str, *, eyebrow: str = "Research workspace") -> None:
    st.markdown(
        f'<div class="crm-header"><div class="crm-eyebrow">{escape(eyebrow)}</div><h1>{escape(title)}</h1><p>{escape(description)}</p></div>',
        unsafe_allow_html=True,
    )


def workflow_navigation(
    *,
    previous: tuple[str, str] | None = None,
    next_step: tuple[str, str] | None = None,
    note: str | None = None,
    next_disabled: bool = False,
) -> None:
    """Render consistent navigation between numbered research workflow pages."""
    st.divider()
    st.subheader("Continue the workflow")
    if note:
        st.caption(note)

    if previous and next_step:
        previous_column, next_column = st.columns(2)
    elif previous:
        previous_column, next_column = st.container(), None
    else:
        previous_column, next_column = None, st.container()

    if previous and previous_column:
        label, page = previous
        with previous_column:
            if st.button(
                f"Previous: {label}",
                use_container_width=True,
                key=f"workflow_previous_{page}",
            ):
                st.switch_page(page)

    if next_step and next_column:
        label, page = next_step
        with next_column:
            if st.button(
                f"Next: {label}",
                type="primary",
                use_container_width=True,
                disabled=next_disabled,
                key=f"workflow_next_{page}",
            ):
                st.switch_page(page)
