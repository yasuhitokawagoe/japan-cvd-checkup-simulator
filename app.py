"""Public, mobile-first health-check flow mounted by Streamlit at /checkup."""
from __future__ import annotations

import hashlib
import html
import os
import sys
import uuid
from pathlib import Path
from urllib.parse import urlencode

import numpy as np
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from calc_engine_outcomes import OutcomesEngine
from checkup_analytics import aggregate_events, record_event
from checkup_pdf import create_checkup_handout
from lifestyle_interventions import DIET_EFFECTS, EXERCISE_EFFECTS, apply_lifestyle_effects
from meds_catalog import apply_meds_to_targets, load_meds_catalog

st.set_page_config(page_title="健診から未来をみる", page_icon="✦", layout="centered",
                   initial_sidebar_state="collapsed")

st.markdown("""
<style>
:root{--ink:#143f35;--muted:#597067;--green:#176b5b;--green2:#23856f;--mint:#eaf4ee;--line:#d7e5dc;--warm:#f5f8f6;--red:#cf5b52;--blue:#477da8}
[data-testid="stHeader"]{background:transparent}.stApp{background:var(--warm)}
.block-container{max-width:1180px;padding:1.2rem 1.35rem 5rem}h1,h2,h3{color:var(--ink);letter-spacing:-.025em}
h1{font-size:clamp(2rem,8vw,3rem)!important;line-height:1.2!important}.eyebrow{color:var(--green2);font-size:.78rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase}
.lead{font-size:1.05rem;line-height:1.9;color:#425c53}.soft{color:var(--muted);font-size:.9rem}.hero{padding:2rem 1.35rem 1.6rem;background:linear-gradient(125deg,#176b5b 0%,#23856f 62%,#62aa73 100%);border-radius:24px;color:white;box-shadow:0 15px 35px rgba(23,107,91,.18);margin:.5rem 0 1.2rem}.hero h1,.hero .lead,.hero .soft,.hero .eyebrow{color:white!important}.hero .soft{opacity:.9}
.hero-mark{width:46px;height:46px;border-radius:15px;background:#ffffff24;color:white;display:grid;place-items:center;font-size:21px;margin-bottom:1.35rem}
.trust{display:flex;gap:.6rem;flex-wrap:wrap;margin:1.2rem 0}.pill{background:white;border:1px solid var(--line);border-radius:999px;padding:.45rem .75rem;color:#526777;font-size:.82rem}
.hero .pill{background:#ffffff20;border-color:#ffffff40;color:#fff}.panel{background:#fff;border:1px solid var(--line);border-radius:18px;padding:1.2rem;box-shadow:0 7px 22px rgba(31,74,61,.06);margin:.8rem 0}
.risk-number{font-size:2.25rem;font-weight:800;color:var(--ink);line-height:1}.risk-label{font-size:.82rem;color:var(--muted);margin-bottom:.55rem;font-weight:650}
.delta{display:inline-block;background:var(--mint);color:#0d6b64;border-radius:8px;padding:.28rem .5rem;font-weight:650;font-size:.82rem}
.progress-copy{display:flex;justify-content:space-between;color:var(--muted);font-size:.76rem;margin-bottom:.4rem}.progress-track{height:5px;background:#dfe9e3;border-radius:5px;margin-bottom:1.6rem}.progress-fill{height:5px;background:var(--green2);border-radius:5px}
.summary-row{display:flex;justify-content:space-between;gap:1rem;padding:.75rem 0;border-bottom:1px solid #edf1f2}.summary-row:last-child{border:0}.summary-row span:first-child{color:var(--muted)}
.notice{border-left:3px solid var(--green2);padding:.2rem 0 .2rem 1rem;color:#526777;line-height:1.7;font-size:.9rem}
.cvd-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:.7rem;margin:1rem 0}.cvd-card{background:#fff;border:1px solid var(--line);border-radius:17px;padding:1rem;box-shadow:0 5px 16px rgba(31,74,61,.05)}.cvd-horizon{font-size:.76rem;font-weight:750;color:var(--green);margin-bottom:.8rem}.cvd-pair{display:flex;justify-content:space-between;gap:.5rem}.cvd-pair span{font-size:.74rem;color:var(--muted)}.cvd-pair strong{display:block;font-size:1.38rem;color:var(--ink);margin-top:.2rem}.reference-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:.55rem;margin:1rem 0}.reference-item{background:#eef7f2;border:1px solid #cfe3d7;border-radius:13px;padding:.75rem}.reference-item span{font-size:.73rem;color:#547066;font-weight:700}.reference-item strong{font-size:1.2rem;color:#143f35;display:block}.reference-item small{color:#6f817a}
.dashboard-head{background:linear-gradient(125deg,#176b5b,#23856f 65%,#62aa73);padding:1.2rem 1.35rem;border-radius:20px;color:white;margin-bottom:1rem;box-shadow:0 10px 28px rgba(23,107,91,.16)}.dashboard-head h1{color:white!important;font-size:1.75rem!important;margin:.1rem 0}.dashboard-head p{margin:0;color:#eefbf5}.section-kicker{font-size:.75rem;letter-spacing:.1em;color:var(--green);font-weight:800;text-transform:uppercase}.live-dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#74d69a;margin-right:.4rem}.result-band{display:grid;grid-template-columns:repeat(3,1fr);gap:.65rem;margin:.7rem 0}.result-tile{background:#fff;border:1px solid var(--line);padding:.85rem;border-radius:14px}.result-tile span{display:block;color:var(--muted);font-size:.75rem}.result-tile strong{display:block;color:var(--ink);font-size:1.55rem;margin:.15rem 0}.result-tile small{color:var(--green);font-weight:700}
.stButton>button,.stDownloadButton>button{border-radius:12px!important;min-height:3.15rem;font-weight:700;border-color:#cbd9dc;width:100%}
.stButton>button[kind="primary"]{background:var(--green);border-color:var(--green);box-shadow:0 8px 22px #176b5b26}
[data-testid="stNumberInput"] input{font-size:1.25rem;font-weight:650;min-height:3rem}.stRadio label,.stCheckbox label{line-height:1.5}
div[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);padding:.8rem;border-radius:14px}
@media(max-width:700px){.block-container{padding:.7rem .85rem 4rem}.panel{border-radius:17px}.hero{padding:1.3rem 1.05rem}.cvd-grid{grid-template-columns:1fr}.reference-strip{grid-template-columns:repeat(2,1fr)}.result-band{grid-template-columns:1fr}.dashboard-head{padding:1rem}.dashboard-head h1{font-size:1.4rem!important}}
@media print{[data-testid="stHeader"],.stButton,button{display:none!important}.block-container{max-width:100%;padding:0}.panel{box-shadow:none}}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def engine() -> OutcomesEngine:
    return OutcomesEngine(str(ROOT / "config.yaml"))


@st.cache_data(show_spinner=False)
def catalog():
    return load_meds_catalog(str(ROOT / "降圧薬詳細_Ca-ARNI_薬価付き_日本語表_英語タイトル引用付き.xlsx"),
                             str(ROOT / "LDL_HbA1c_用量別_薬価付き_日本語表_英語タイトル引用付き.xlsx"))


def qp(name: str) -> str:
    value = st.query_params.get(name, "")
    return value[0] if isinstance(value, list) else str(value)


if "checkup_session_id" not in st.session_state:
    st.session_state.checkup_session_id = uuid.uuid4().hex
if "checkup_stage" not in st.session_state:
    st.session_state.checkup_stage = "landing"
if "checkup_referral_id" not in st.session_state:
    st.session_state.checkup_referral_id = uuid.uuid4().hex[:12]
if "checkup_events" not in st.session_state:
    st.session_state.checkup_events = set()

# Every field starts with a clinically neutral reference value. Streamlit can
# leave a keyed widget as None after navigation; normalise it before any cast.
DEFAULTS = {
    "c_age": 60, "c_sex": "male", "c_height": 170.0, "c_weight": 65.0,
    "c_bmi": 65.0 / 1.7**2, "c_sbp": 120, "c_dbp": 80,
    "c_bp_med": "no", "c_ldl": 100, "c_hdl": 60, "c_tg": 100,
    "c_lipid_med": "no", "c_a1c": 5.7, "c_diabetes": "no",
    "c_smoking": "never", "c_cigs": 0, "c_smoke_years": 0,
    "c_quit_years": 0, "c_egfr_known": True, "c_egfr": 80.0,
    "c_sbp_target": 120, "c_ldl_target_live": 100, "c_a1c_target_live": 5.7,
}
CTX = {
    "session_id": st.session_state.checkup_session_id,
    "source": qp("source"), "campaign": qp("campaign"), "facility_id": qp("facility_id"),
    "referral_id": st.session_state.checkup_referral_id, "parent_referral_id": qp("ref"),
}


def track(event: str, once_key: str | None = None) -> None:
    key = once_key or event
    if key not in st.session_state.checkup_events:
        record_event(event, CTX)
        st.session_state.checkup_events.add(key)


def navigate(stage: str, event: str | None = None) -> None:
    if event:
        track(event)
    st.session_state.checkup_stage = stage
    st.rerun()


def progress(step: int, total: int = 7) -> None:
    st.markdown(f'<div class="progress-copy"><span>健診結果から入力</span><span>{step} / {total}</span></div><div class="progress-track"><div class="progress-fill" style="width:{100*step/total:.0f}%"></div></div>', unsafe_allow_html=True)


def val(key: str, default=None):
    fallback = DEFAULTS.get(key, default)
    value = st.session_state.get(key, fallback)
    return fallback if value is None else value


def nudge(key: str, amount: float, low: float, high: float) -> None:
    current = float(val(key, DEFAULTS.get(key, low)))
    value = min(high, max(low, current + amount))
    st.session_state[key] = int(value) if isinstance(DEFAULTS.get(key), int) else value


def quick_slider(label: str, key: str, low: float, high: float, step: float, jump: float, unit: str) -> float:
    """Slider with one-tap adjustments, matching the DM-care interaction."""
    st.markdown(f"**{label}**　<span class='soft'>{unit}</span>", unsafe_allow_html=True)
    if key in st.session_state and st.session_state.get(key) is not None:
        value = st.slider(label, min_value=low, max_value=high, step=step, key=key, label_visibility="collapsed")
    else:
        value = st.slider(label, min_value=low, max_value=high, value=val(key), step=step, key=key, label_visibility="collapsed")
    left, right = st.columns(2)
    def button_label(delta: float) -> str:
        return f"{delta:+g}".replace("+", "＋").replace("-", "−")
    left.button(button_label(-jump), key=f"{key}_minus", on_click=nudge, args=(key, -jump, low, high), use_container_width=True)
    right.button(button_label(jump), key=f"{key}_plus", on_click=nudge, args=(key, jump, low, high), use_container_width=True)
    return value


def risk_params(targets: dict | None = None) -> dict:
    smoking = val("c_smoking", "never")
    target = targets or {"sbp": val("c_sbp", 130), "ldl": val("c_ldl", 140), "a1c": val("c_a1c", 5.8),
                         "bmi": val("c_bmi", 23.9), "quit": False}
    return dict(sex=val("c_sex", "male"), start_age=int(val("c_age", 52)),
                sbp_now=float(val("c_sbp", 130)), sbp_target=float(target["sbp"]),
                ldl_now_mg=float(val("c_ldl", 140)), ldl_target_mg=float(target["ldl"]),
                hba1c_now=float(val("c_a1c", 5.8)), hba1c_target=float(target["a1c"]),
                smoking_status=smoking, cigs_per_day=int(val("c_cigs", 0)),
                years_smoked=float(val("c_smoke_years", 0)), years_since_quit=float(val("c_quit_years", 0)),
                assume_quit_today_in_target=bool(target.get("quit", False)), bmi_now=val("c_bmi", 23.9),
                bmi_target=target.get("bmi", val("c_bmi", 23.9)), egfr_now=val("c_egfr"),
                egfr_target=val("c_egfr"), acr_now=None, acr_target=None)


def risks(targets: dict | None = None) -> dict:
    out = {}
    age = int(val("c_age", 52))
    horizons = {"10年": min(10, 110-age), "20年": min(20, 110-age), "30年": min(30, 110-age)}
    for label, years in horizons.items():
        if years <= 0:
            continue
        out[label] = {}
        for outcome in ("mi", "stroke", "mortality"):
            out[label][outcome] = engine().cumulative_incidence_with_ci(outcome=outcome, years=years, **risk_params(targets))["point"]
    return out


stage = st.session_state.checkup_stage
if qp("mode") == "handout":
    stage = "handout"
# Migrate sessions left on the former seven-screen wizard to the live dashboard.
if stage in {"consent", "basic", "bp", "lipid", "other", "confirm", "result", "simulate"}:
    stage = "dashboard"
    st.session_state.checkup_stage = "dashboard"

if qp("admin") == "1":
    st.markdown('<p class="eyebrow">Operations</p>', unsafe_allow_html=True)
    st.title("健診フロー 利用状況")
    st.caption("健診値などの個人データは記録していません。施設・キャンペーン別のイベント集計のみです。")
    rows = aggregate_events()
    if rows:
        import pandas as pd
        frame = pd.DataFrame(rows)
        st.dataframe(frame.pivot_table(index=["facility_id", "campaign"], columns="event", values="count", fill_value=0), width="stretch")
    else:
        st.info("まだイベントはありません。")
    st.stop()

if stage == "dashboard":
    track("consent_completed", "dashboard_opened")
    st.markdown('''<div class="dashboard-head"><div class="section-kicker" style="color:#d8f5e5"><span class="live-dot"></span>LIVE SIMULATION</div><h1>健診結果から、これからを考える</h1><p>入力を変えると、将来リスクがその場で更新されます。</p></div>''', unsafe_allow_html=True)
    with st.expander("利用前の注意事項", expanded=False):
        st.markdown("本サービスは医療診断ではなく、研究データに基づく推定です。医薬品を自己判断で開始・中止・変更せず、治療は医療専門職にご相談ください。")

    input_col, result_col = st.columns([.88, 1.22], gap="large")
    with input_col:
        st.markdown('<div class="section-kicker">INPUT</div>', unsafe_allow_html=True)
        st.subheader("健診値と目標")
        profile_a, profile_b = st.columns(2)
        profile_a.selectbox("性別", ["male", "female"], format_func=lambda x: "男性" if x == "male" else "女性", key="c_sex")
        profile_b.number_input("年齢（歳）", 20, 95, value=int(val("c_age")), step=1, key="c_age")

        st.markdown("#### 現在の値")
        quick_slider("上の血圧（収縮期）", "c_sbp", 90, 200, 1, 10, "mmHg")
        quick_slider("LDLコレステロール", "c_ldl", 50, 250, 1, 10, "mg/dL")
        quick_slider("HbA1c", "c_a1c", 3.0, 12.0, .1, .5, "%")

        st.markdown("#### 目標値")
        quick_slider("上の血圧（収縮期）", "c_sbp_target", 90, 160, 1, 10, "mmHg")
        quick_slider("LDLコレステロール", "c_ldl_target_live", 50, 160, 1, 10, "mg/dL")
        quick_slider("HbA1c", "c_a1c_target_live", 3.0, 9.0, .1, .5, "%")

        with st.expander("喫煙・体格・腎機能"):
            st.radio("喫煙", ["never", "current", "former"], format_func=lambda x:{"never":"吸わない","current":"現在吸っている","former":"以前吸っていた"}[x], key="c_smoking", horizontal=True)
            if val("c_smoking") in {"current", "former"}:
                sm1, sm2 = st.columns(2)
                sm1.number_input("1日の本数", 0, 80, step=1, key="c_cigs")
                sm2.number_input("喫煙年数", 0, 70, step=1, key="c_smoke_years")
            if val("c_smoking") == "former":
                st.number_input("禁煙からの年数", 0, 70, step=1, key="c_quit_years")
            body1, body2 = st.columns(2)
            body1.number_input("身長（cm）", 120.0, 210.0, value=float(val("c_height")), step=.5, key="c_height")
            body2.number_input("体重（kg）", 30.0, 180.0, value=float(val("c_weight")), step=.5, key="c_weight")
            st.number_input("eGFR", 1.0, 150.0, value=float(val("c_egfr")), step=1.0, key="c_egfr")
            st.session_state.c_bmi = float(val("c_weight")) / (float(val("c_height")) / 100) ** 2
            st.caption(f'BMI {val("c_bmi"):.1f}')

        with st.expander("生活習慣・薬剤を追加"):
            diet_keys=st.multiselect("食生活", list(DIET_EFFECTS), format_func=lambda k:DIET_EFFECTS[k].label, key="live_diets")
            exercise=st.selectbox("運動", [None,*EXERCISE_EFFECTS], format_func=lambda k:"選択しない" if k is None else EXERCISE_EFFECTS[k].label, key="live_exercise")
            try:
                meds=catalog()
                bp_drugs=st.multiselect("降圧薬", [m["key"] for m in meds["sbp"]], key="live_bp_drugs")
                ldl_drugs=st.multiselect("脂質低下薬", [m["key"] for m in meds["ldl"]], key="live_ldl_drugs")
                a1c_drugs=st.multiselect("糖尿病薬", [m["key"] for m in meds["hba1c"]], key="live_a1c_drugs")
            except Exception:
                bp_drugs=ldl_drugs=a1c_drugs=[]
                st.warning("薬剤カタログを読み込めませんでした。")
        horizon=st.selectbox("予測期間", [10,20,30], index=1, format_func=lambda y:f"{y}年", key="live_horizon")

    targets={"sbp":float(val("c_sbp_target")),"ldl":float(val("c_ldl_target_live")),"a1c":float(val("c_a1c_target_live")),"bmi":float(val("c_bmi")),"quit":val("c_smoking")=="current"}
    if bp_drugs or ldl_drugs or a1c_drugs:
        selected_bp=[m for m in meds["sbp"] if m["key"] in bp_drugs]
        selected_ldl=[m for m in meds["ldl"] if m["key"] in ldl_drugs]
        selected_a1c=[m for m in meds["hba1c"] if m["key"] in a1c_drugs]
        med_targets=apply_meds_to_targets(targets["sbp"],targets["ldl"],targets["a1c"],selected_bp,selected_ldl,selected_a1c)
        targets.update(sbp=med_targets["sbp_target"],ldl=med_targets["ldl_target"],a1c=med_targets["a1c_target"])
    lifestyle=apply_lifestyle_effects(sbp=targets["sbp"],ldl=targets["ldl"],a1c=targets["a1c"],diet_keys=diet_keys,exercise_key=exercise,diabetes_context=val("c_diabetes")=="yes" or val("c_a1c")>=6.5)
    targets.update(sbp=lifestyle["sbp"],ldl=lifestyle["ldl"],a1c=lifestyle["a1c"])

    live_results={}
    for outcome in ("mi","stroke","mortality"):
        live_results[outcome]=engine().cumulative_incidence_with_ci(outcome=outcome,years=int(horizon),**risk_params(targets))["point"]

    with result_col:
        track("result_viewed", "live_result")
        st.markdown('<div class="section-kicker"><span class="live-dot"></span>REAL-TIME RESULT</div>', unsafe_allow_html=True)
        st.subheader("リアルタイム予測")
        tiles=[]
        for outcome,name in (("mi","心筋梗塞"),("stroke","脳卒中"),("mortality","全死亡")):
            before=100*live_results[outcome]["baseline"]; after=100*live_results[outcome]["target"]; diff=after-before
            change_text=f'{abs(diff):.1f} pt減少' if diff < 0 else (f'{diff:.1f} pt増加' if diff > 0 else '変化なし')
            tiles.append(f'<div class="result-tile"><span>{horizon}年・{name}</span><strong>{after:.1f}%</strong><small>現在 {before:.1f}% ／ {change_text}</small></div>')
        st.markdown('<div class="result-band">'+''.join(tiles)+'</div>',unsafe_allow_html=True)
        st.caption("全死亡には、心血管疾患以外のがんやその他の疾患も含みます。")

        xs=list(range(0,int(horizon)+1)); fig=go.Figure()
        for outcome,name,color in (("mi","心筋梗塞","#cf5b52"),("stroke","脳卒中","#477da8")):
            before_curve=[];after_curve=[]
            for year in xs:
                if year==0: before_curve.append(0);after_curve.append(0)
                else:
                    rr=engine().cumulative_incidence_with_ci(outcome=outcome,years=year,**risk_params(targets))["point"]
                    before_curve.append(100*rr["baseline"]);after_curve.append(100*rr["target"])
            fig.add_trace(go.Scatter(x=xs,y=before_curve,name=f"{name}・現在",line=dict(color=color,width=2,dash="dot")))
            fig.add_trace(go.Scatter(x=xs,y=after_curve,name=f"{name}・目標",line=dict(color=color,width=3)))
        fig.update_layout(height=410,margin=dict(l=12,r=12,t=28,b=12),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#fff",xaxis_title="現在からの年数",yaxis_title="累積リスク（%）",hovermode="x unified",legend=dict(orientation="h",y=1.12))
        st.plotly_chart(fig,width="stretch",config={"displayModeBar":False})

        st.markdown("#### 入力と目標の確認")
        check_cols=st.columns(3)
        for col,label,now,target,unit in ((check_cols[0],"上の血圧",val("c_sbp"),targets["sbp"],"mmHg"),(check_cols[1],"LDL",val("c_ldl"),targets["ldl"],"mg/dL"),(check_cols[2],"HbA1c",val("c_a1c"),targets["a1c"],"%")):
            col.metric(label,f"{now:g} {unit}",delta=f"目標 {target:.1f} {unit}",delta_color="off")
        st.markdown('<div class="notice">入力変更は即時反映されます。表示値は研究データに基づく平均的な推定で、個人の発症を断定するものではありません。</div>',unsafe_allow_html=True)
    st.stop()

if stage == "landing":
    track("landing_view")
    campaign = qp("campaign").upper()
    alt = {"A": "この健診結果で、あなたの20年後はどう変わる？", "B": "あなたに一番効果の大きい健康対策は？"}.get(campaign)
    st.markdown(f'''<div class="hero"><div class="hero-mark">✦</div><p class="eyebrow">Your health, in perspective</p><h1>健診、おつかれさまでした。</h1><p class="lead">{html.escape(alt or "その数字を「未来」にしてみませんか？")}<br><span class="soft">今の状態と、生活や治療を変えた未来を比べられます。</span></p><div class="trust"><span class="pill">約3分</span><span class="pill">登録不要</span><span class="pill">入力値は解析に保存しません</span></div></div>''', unsafe_allow_html=True)
    if st.button("健診結果を見ながら始める　→", type="primary"):
        navigate("dashboard", "start_clicked")
    with st.expander("どんなサービス？"):
        st.write("健診の数字が将来にどう影響し、何を変えると推定リスクがどの程度変わるかを、グラフで比較するシミュレーターです。診断や治療の推奨を行うものではありません。")
    st.stop()

if stage == "consent":
    progress(1)
    st.markdown('<p class="eyebrow">Before you begin</p>', unsafe_allow_html=True)
    st.title("はじめに、ご確認ください")
    st.markdown('<div class="notice">本サービスは医療診断を行わず、将来の発症を確実に予測するものではありません。<br><br>表示値は疫学研究・臨床研究等をもとにした推定値です。医薬品の開始・中止・変更を自己判断せず、治療は医師などの医療専門職にご相談ください。</div>', unsafe_allow_html=True)
    ok = st.checkbox("内容を確認しました")
    if st.button("次へ", type="primary", disabled=not ok):
        navigate("basic", "consent_completed")
    st.stop()

if stage == "basic":
    progress(2); st.title("まず、基本情報から")
    st.caption("健診結果に記載された内容を入力してください。")
    with st.form("basic_form"):
        age = st.number_input("年齢", 20, 95, val("c_age", 52), step=1, key="c_age", help="歳")
        st.radio("性別", ["male", "female"], index=0, format_func=lambda x: "男性" if x == "male" else "女性", horizontal=True, key="c_sex")
        c1, c2 = st.columns(2)
        c1.number_input("身長（cm）", 120.0, 210.0, val("c_height", 165.0), .1, key="c_height")
        c2.number_input("体重（kg）", 30.0, 180.0, val("c_weight", 65.0), .1, key="c_weight")
        submitted = st.form_submit_button("次へ", type="primary")
    if submitted:
        st.session_state.c_bmi = st.session_state.c_weight / (st.session_state.c_height / 100) ** 2
        track("basic_input_completed"); navigate("bp")
    st.stop()

if stage == "bp":
    progress(3); st.title("血圧")
    st.caption("上の血圧・下の血圧を、そのまま転記してください。")
    with st.form("bp_form"):
        c1, c2 = st.columns(2)
        c1.number_input("収縮期（上）", 70, 250, val("c_sbp", 130), key="c_sbp", help="mmHg")
        c2.number_input("拡張期（下）", 40, 150, val("c_dbp", 80), key="c_dbp", help="mmHg")
        st.radio("降圧薬", ["no", "yes", "unknown"], index=0, format_func=lambda x:{"no":"使用していない","yes":"使用している","unknown":"分からない"}[x], key="c_bp_med")
        submitted = st.form_submit_button("次へ", type="primary")
    if submitted: navigate("lipid")
    st.stop()

if stage == "lipid":
    progress(4); st.title("コレステロール")
    st.caption("LDL-Cは現在の計算モデルで必要です。HDL-Cなどは確認用に表示します。")
    with st.form("lipid_form"):
        st.number_input("LDLコレステロール（mg/dL）", 20, 400, val("c_ldl", 140), key="c_ldl")
        c1,c2=st.columns(2)
        c1.number_input("HDL-C（任意）", 0, 200, val("c_hdl", 0), key="c_hdl", help="不明なら0")
        c2.number_input("中性脂肪（任意）", 0, 1000, val("c_tg", 0), key="c_tg", help="不明なら0")
        st.radio("脂質低下薬", ["no","yes","unknown"], index=0, format_func=lambda x:{"no":"使用していない","yes":"使用している","unknown":"分からない"}[x], key="c_lipid_med")
        submitted=st.form_submit_button("次へ",type="primary")
    if submitted: navigate("other")
    st.stop()

if stage == "other":
    progress(5); st.title("その他の項目")
    with st.form("other_form"):
        st.number_input("HbA1c（%）", 3.0, 20.0, val("c_a1c", 5.8), .1, key="c_a1c")
        st.radio("糖尿病", ["no","yes","unknown"], index=0, format_func=lambda x:{"no":"なし","yes":"あり","unknown":"分からない"}[x], horizontal=True, key="c_diabetes")
        st.radio("喫煙", ["never","current","former"], index=0, format_func=lambda x:{"never":"吸わない","current":"現在吸っている","former":"以前吸っていた"}[x], key="c_smoking")
        if val("c_smoking", "never") in {"current","former"}:
            c1,c2=st.columns(2); c1.number_input("1日の本数",0,80,val("c_cigs",10),key="c_cigs"); c2.number_input("喫煙年数",0,70,val("c_smoke_years",20),key="c_smoke_years")
        if val("c_smoking", "never") == "former":
            st.number_input("禁煙してから（年）",0,70,val("c_quit_years",5),key="c_quit_years")
        known = st.checkbox("eGFRが分かる", value=val("c_egfr_known", False), key="c_egfr_known")
        if known: st.number_input("eGFR（mL/min/1.73㎡）",1.0,150.0,val("c_egfr",75.0),.1,key="c_egfr")
        submitted=st.form_submit_button("入力内容を確認",type="primary")
    if submitted:
        if not known: st.session_state.c_egfr=None
        track("full_input_completed"); navigate("confirm")
    st.stop()

if stage == "confirm":
    progress(6); st.title("入力内容の確認")
    smoke_label={"never":"なし","current":"あり","former":"過去にあり"}[val("c_smoking", "never")]
    rows=[("年齢・性別",f'{val("c_age",52)}歳・{"男性" if val("c_sex","male")=="male" else "女性"}'),("BMI",f'{val("c_bmi",23.9):.1f}'),("血圧",f'{val("c_sbp",130)} / {val("c_dbp",80)} mmHg'),("LDL-C",f'{val("c_ldl",140)} mg/dL'),("HbA1c",f'{val("c_a1c",5.8):.1f}%'),("喫煙",smoke_label),("eGFR",f'{val("c_egfr"):.1f}' if val("c_egfr") else "未入力")]
    st.markdown('<div class="panel">'+''.join(f'<div class="summary-row"><span>{a}</span><strong>{b}</strong></div>' for a,b in rows)+'</div>',unsafe_allow_html=True)
    if st.button("この内容で未来を見る",type="primary"):
        track("result_viewed"); navigate("result")
    if st.button("入力を修正する"):
        navigate("basic")
    st.stop()

if stage in {"result", "simulate", "handoff"}:
    current = risks()
    if stage == "result":
        st.markdown('<p class="eyebrow">Your cardiovascular outlook</p>',unsafe_allow_html=True)
        st.title("健診結果からみた、これからの心血管リスク")
        st.caption("現在の状態が続いた場合の推定です。診断や発症の断定ではありません。")

        reference = {"sbp": 120.0, "ldl": 100.0, "a1c": 5.7, "bmi": 22.0, "quit": val("c_smoking") == "current"}
        ref_items = [
            ("収縮期血圧", f'{val("c_sbp"):.0f}', f'基準 120 / 差 {val("c_sbp")-120:+.0f}'),
            ("LDL-C", f'{val("c_ldl"):.0f}', f'基準 100 / 差 {val("c_ldl")-100:+.0f}'),
            ("HbA1c", f'{val("c_a1c"):.1f}%', f'基準 5.7 / 差 {val("c_a1c")-5.7:+.1f}'),
            ("BMI", f'{val("c_bmi"):.1f}', f'基準 22 / 差 {val("c_bmi")-22:+.1f}'),
        ]
        st.markdown('<div class="reference-strip">'+''.join(f'<div class="reference-item"><span>{a}</span><strong>{b}</strong><small>{c}</small></div>' for a,b,c in ref_items)+'</div>',unsafe_allow_html=True)

        st.markdown("### 心血管イベント")
        st.caption("心筋梗塞と脳卒中を同じセクションで表示しています。医学的根拠なく加算した合計値は作っていません。")
        cards=[]
        for label,data in current.items():
            cards.append(f'<div class="cvd-card"><div class="cvd-horizon">今後 {label}</div><div class="cvd-pair"><div><span>心筋梗塞</span><strong>{100*data["mi"]["baseline"]:.1f}%</strong></div><div><span>脳卒中</span><strong>{100*data["stroke"]["baseline"]:.1f}%</strong></div></div></div>')
        st.markdown('<div class="cvd-grid">'+''.join(cards)+'</div>',unsafe_allow_html=True)

        age=int(val("c_age", 60)); max_year=max(1,min(30,110-age)); xs=list(range(0,max_year+1)); curves={"mi":[],"stroke":[]}; bands={"mi":([],[]),"stroke":([],[])}
        for outcome in ("mi","stroke"):
            for y in xs:
                if y == 0:
                    curves[outcome].append(0.0); bands[outcome][0].append(0.0); bands[outcome][1].append(0.0)
                else:
                    result=engine().cumulative_incidence_with_ci(outcome=outcome,years=y,**risk_params())
                    curves[outcome].append(100*result["point"]["baseline"]); bands[outcome][0].append(100*result["lower"]["baseline"]); bands[outcome][1].append(100*result["upper"]["baseline"])
        fig=go.Figure()
        colors={"mi":"#cf5b52","stroke":"#477da8"}; names={"mi":"心筋梗塞","stroke":"脳卒中"}
        for outcome in ("mi","stroke"):
            fig.add_trace(go.Scatter(x=xs,y=bands[outcome][1],line=dict(width=0),showlegend=False,hoverinfo="skip"))
            fig.add_trace(go.Scatter(x=xs,y=bands[outcome][0],line=dict(width=0),fill="tonexty",fillcolor="rgba(120,140,140,.10)",showlegend=False,hoverinfo="skip"))
            fig.add_trace(go.Scatter(x=xs,y=curves[outcome],mode="lines",name=names[outcome],line=dict(color=colors[outcome],width=3),hovertemplate=f'{names[outcome]} %{{y:.1f}}%<extra></extra>'))
        fig.update_layout(height=390,margin=dict(l=12,r=12,t=25,b=15),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#ffffff",xaxis_title="現在からの年数",yaxis_title="累積リスク（%）",hovermode="x unified",legend=dict(orientation="h",y=1.1),font=dict(family="sans-serif",color="#526777"))
        st.plotly_chart(fig,width="stretch",config={"displayModeBar":False}); track("trajectory_viewed")
        with st.expander("数値一覧と95%推定区間"):
            import pandas as pd
            detail_rows=[]
            for label,years in (("10年",min(10,110-age)),("20年",min(20,110-age)),("30年",min(30,110-age))):
                for outcome,outcome_name in (("mi","心筋梗塞"),("stroke","脳卒中")):
                    result=engine().cumulative_incidence_with_ci(outcome=outcome,years=years,**risk_params())
                    detail_rows.append({"期間":label,"心血管イベント":outcome_name,"推定リスク":f'{100*result["point"]["baseline"]:.1f}%',"95%推定区間":f'{100*result["lower"]["baseline"]:.1f}–{100*result["upper"]["baseline"]:.1f}%'})
            st.dataframe(pd.DataFrame(detail_rows),hide_index=True,width="stretch")
        with st.expander("全死亡の推定も確認する"):
            st.caption("全死亡には、心血管疾患だけでなく、がんやその他の疾患による死亡も含まれます。")
            death_cols=st.columns(3)
            for col,(label,data) in zip(death_cols,current.items()): col.metric(label,f'{100*data["mortality"]["baseline"]:.1f}%')
        st.markdown('<div class="notice">薄い帯は95%推定区間です。個人の発症を決定するものではありません。表示期間は既存モデルが通常版で扱う範囲に合わせ、10年・20年・30年としています。</div>',unsafe_allow_html=True)
        st.write("");
        if st.button("未来を変えてみる　→",type="primary"): navigate("simulate")
        st.stop()

    if stage == "simulate":
        st.markdown('<p class="eyebrow">Shape a scenario</p>',unsafe_allow_html=True); st.title("未来を変えてみる")
        st.caption("比較したいものを選んでください。選択は治療の推奨ではありません。")
        with st.container(border=True):
            st.subheader("暮らしから変える")
            diet_keys=st.multiselect("食生活",list(DIET_EFFECTS),format_func=lambda k:DIET_EFFECTS[k].label,key="c_diets")
            exercise=st.selectbox("運動",[None,*EXERCISE_EFFECTS],format_func=lambda k:"選択しない" if k is None else EXERCISE_EFFECTS[k].label,key="c_exercise")
            quit_smoke=st.checkbox("禁煙した場合",disabled=val("c_smoking")!="current",key="c_quit")
        if diet_keys or exercise or quit_smoke: track("lifestyle_intervention_clicked",f'lifestyle_{hash(str((diet_keys,exercise,quit_smoke)))}')
        with st.container(border=True):
            st.subheader("検査値を改善した場合")
            improve_bp=st.checkbox("血圧を改善した場合",key="c_improve_bp")
            bp_target=st.slider("収縮期血圧",90,min(180,int(val("c_sbp"))),min(130,int(val("c_sbp"))),key="c_bp_target",disabled=not improve_bp)
            improve_ldl=st.checkbox("LDLコレステロールを改善した場合",key="c_improve_ldl")
            ldl_target=st.slider("LDL-C",40,min(250,int(val("c_ldl"))),min(100,int(val("c_ldl"))),key="c_ldl_target",disabled=not improve_ldl)
            improve_a1c=st.checkbox("HbA1cを改善した場合",key="c_improve_a1c")
            a1c_target=st.slider("HbA1c",3.0,float(val("c_a1c")),min(7.0,float(val("c_a1c"))),step=.1,key="c_a1c_target",disabled=not improve_a1c)
            if improve_bp or improve_ldl or improve_a1c: track("medical_intervention_clicked",f'medical_{improve_bp}_{improve_ldl}_{improve_a1c}')
            with st.expander("具体的な治療方法も比較できます"):
                try:
                    meds=catalog(); bp_opts=[m["key"] for m in meds["sbp"]]; ldl_opts=[m["key"] for m in meds["ldl"]]; a1c_opts=[m["key"] for m in meds["hba1c"]]
                    bp_drugs=st.multiselect("降圧薬",bp_opts,key="c_bp_drugs"); ldl_drugs=st.multiselect("脂質低下薬",ldl_opts,key="c_ldl_drugs"); a1c_drugs=st.multiselect("糖尿病薬",a1c_opts,key="c_a1c_drugs")
                except Exception:
                    bp_drugs=[];ldl_drugs=[];a1c_drugs=[];st.info("薬剤カタログを読み込めませんでした。")
                if bp_drugs or ldl_drugs or a1c_drugs: track("specific_drug_clicked",f'drugs_{hash(str((bp_drugs,ldl_drugs,a1c_drugs)))}')
        base_targets={"sbp":float(val("c_sbp")),"ldl":float(val("c_ldl")),"a1c":float(val("c_a1c")),"bmi":val("c_bmi"),"quit":quit_smoke}
        if improve_bp: base_targets["sbp"]=float(bp_target)
        if improve_ldl: base_targets["ldl"]=float(ldl_target)
        if improve_a1c: base_targets["a1c"]=float(a1c_target)
        if bp_drugs or ldl_drugs or a1c_drugs:
            selected_bp=[m for m in meds["sbp"] if m["key"] in bp_drugs]; selected_ldl=[m for m in meds["ldl"] if m["key"] in ldl_drugs]; selected_a1c=[m for m in meds["hba1c"] if m["key"] in a1c_drugs]
            med_result=apply_meds_to_targets(float(base_targets["sbp"]),float(base_targets["ldl"]),float(base_targets["a1c"]),selected_bp,selected_ldl,selected_a1c)
            base_targets.update(sbp=med_result["sbp_target"],ldl=med_result["ldl_target"],a1c=med_result["a1c_target"])
        lifestyle=apply_lifestyle_effects(sbp=base_targets["sbp"],ldl=base_targets["ldl"],a1c=base_targets["a1c"],diet_keys=diet_keys,exercise_key=exercise,diabetes_context=val("c_diabetes")=="yes" or val("c_a1c")>=6.5)
        base_targets.update(sbp=lifestyle["sbp"],ldl=lifestyle["ldl"],a1c=lifestyle["a1c"])
        selected=bool(diet_keys or exercise or quit_smoke or improve_bp or improve_ldl or improve_a1c or bp_drugs or ldl_drugs or a1c_drugs)
        planned=risks(base_targets)
        st.subheader("選択した未来との比較")
        labels=list(current)
        fig=go.Figure()
        for outcome,name,color in (("mi","心筋梗塞","#cf5b52"),("stroke","脳卒中","#477da8")):
            before=[100*current[k][outcome]["baseline"] for k in labels]
            after=[100*planned[k][outcome]["target"] for k in labels]
            fig.add_trace(go.Bar(name=f"{name}・現在",x=labels,y=before,marker_color=color,opacity=.38))
            fig.add_trace(go.Bar(name=f"{name}・選択後",x=labels,y=after,marker_color=color))
        fig.update_layout(barmode="group",height=390,margin=dict(l=8,r=8,t=15,b=8),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#ffffff",yaxis_title="累積リスク（%）",legend=dict(orientation="h",y=1.16))
        st.plotly_chart(fig,width="stretch",config={"displayModeBar":False})
        if "10年" in current:
            comparison=[]
            for outcome,name in (("mi","心筋梗塞"),("stroke","脳卒中")):
                b=100*current["10年"][outcome]["baseline"]; a=100*planned["10年"][outcome]["target"]
                comparison.append(f'<div><div class="risk-label">10年・{name}</div><div class="risk-number">{b:.1f}% <span style="color:#91a0a8">→</span> {a:.1f}%</div><br><span class="delta">絶対差 {a-b:+.1f}ポイント</span></div>')
            st.markdown('<div class="panel" style="display:grid;grid-template-columns:repeat(2,1fr);gap:1.4rem">'+''.join(comparison)+'</div>',unsafe_allow_html=True)
        chosen=[DIET_EFFECTS[k].label for k in diet_keys]+([EXERCISE_EFFECTS[exercise].label] if exercise else [])+(["禁煙"] if quit_smoke else [])+([f"血圧 {base_targets['sbp']:.0f} mmHg"] if improve_bp or bp_drugs else [])+([f"LDL-C {base_targets['ldl']:.0f} mg/dL"] if improve_ldl or ldl_drugs else [])+([f"HbA1c {base_targets['a1c']:.1f}%"] if improve_a1c or a1c_drugs else [])
        st.session_state.c_plan={"targets":base_targets,"labels":chosen,"risks":planned}
        if selected: track("plan_created",f'plan_{hash(str(chosen))}')
        st.subheader("あなたが選んだ未来")
        st.markdown('<div class="panel">'+(''.join(f'<div class="summary-row"><span>✓</span><strong>{html.escape(x)}</strong></div>' for x in chosen) if chosen else '<span class="soft">介入を選ぶとここに表示されます。</span>')+'</div>',unsafe_allow_html=True)
        st.caption("薬剤の効果は研究データ等から推定した平均的な値で、実際の効果には個人差があります。")
        if st.button("このプランについて医師と相談する",type="primary",disabled=not selected):
            track("doctor_handoff_clicked"); navigate("handoff")
        st.divider(); st.subheader("ご家族の健診結果も確認してみませんか？")
        base_url=qp("base_url") or os.environ.get("PUBLIC_APP_URL", "https://japan-cvd-checkup-simulator.up.railway.app"); share_url=base_url+"?"+urlencode({"source":"family_share","ref":CTX["referral_id"]})
        if st.button("家族に送る"):
            track("family_share_clicked")
            components.html(f'''<button onclick="share()" style="width:100%;height:48px;border:0;border-radius:12px;background:#17324d;color:#fff;font-weight:700">共有メニューを開く</button><script>async function share(){{const d={{title:'健診から未来をみる',text:'健診結果から将来の健康を考えてみませんか？',url:{share_url!r}}};if(navigator.share){{await navigator.share(d)}}else{{await navigator.clipboard.writeText(d.url);document.body.innerHTML='<p style="font-family:sans-serif;color:#147d75">URLをコピーしました</p>'}}}}</script>''',height=58)
            st.code(share_url,language=None)
        st.stop()

    if stage == "handoff":
        plan=val("c_plan",{}); planned=plan.get("risks",current)
        st.markdown('<p class="eyebrow">For consultation</p>',unsafe_allow_html=True);st.title("医師に見せるサマリー")
        st.caption("利用者が比較のために選択したシミュレーションです。処方指示ではありません。")
        st.markdown(f'<div class="panel"><h3>主要健診値</h3><div class="summary-row"><span>年齢・性別</span><strong>{val("c_age")}歳・{"男性" if val("c_sex")=="male" else "女性"}</strong></div><div class="summary-row"><span>血圧</span><strong>{val("c_sbp")} / {val("c_dbp")} mmHg</strong></div><div class="summary-row"><span>LDL-C / HbA1c</span><strong>{val("c_ldl")} mg/dL / {val("c_a1c"):.1f}%</strong></div><div class="summary-row"><span>BMI / eGFR</span><strong>{val("c_bmi"):.1f} / {val("c_egfr") or "未入力"}</strong></div></div>',unsafe_allow_html=True)
        st.subheader("心血管イベントのリスク比較")
        for label in current:
            mi_b=100*current[label]["mi"]["baseline"]; mi_a=100*planned[label]["mi"]["target"]
            st_b=100*current[label]["stroke"]["baseline"]; st_a=100*planned[label]["stroke"]["target"]
            st.markdown(f'<div class="panel"><div class="cvd-horizon">{label}</div><div class="summary-row"><span>心筋梗塞</span><strong>{mi_b:.1f}% → {mi_a:.1f}%（{mi_a-mi_b:+.1f}pt）</strong></div><div class="summary-row"><span>脳卒中</span><strong>{st_b:.1f}% → {st_a:.1f}%（{st_a-st_b:+.1f}pt）</strong></div></div>',unsafe_allow_html=True)
        st.subheader("利用者が選択したプラン")
        for item in plan.get("labels",[]): st.write(f"✓ {item}")
        st.markdown('<div class="notice">推定値には不確実性があり、個人差があります。治療方針は診察・検査結果とあわせてご判断ください。</div>',unsafe_allow_html=True)
        st.button("印刷する",on_click=lambda:None)
        if st.button("シミュレーションに戻る"): navigate("simulate")
        st.stop()

if stage == "handout":
    st.title("健診結果添付用 A4 PDF")
    facility=st.text_input("施設名（任意）")
    url=st.text_input("QRコードのリンク先",value=os.environ.get("PUBLIC_APP_URL", "https://japan-cvd-checkup-simulator.up.railway.app")+"?source=healthcheck")
    pdf=create_checkup_handout(url,facility)
    st.download_button("A4 PDFをダウンロード",pdf,"checkup_qr_handout.pdf","application/pdf",type="primary")
