"""SEG_Maçkolik - Süper Lig + BSL sonuç, puan durumu, fikstür ve gol krallığı."""
import base64
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config.settings import settings
from src.services.football_service import football_service
from src.services.basketball_service import basketball_service
from src.services.standings_service import standings_service
from src.services.scorers_service import scorers_service
from src.utils.date_utils import (
    format_report_date,
    format_date_dots,
    get_today_turkey_date,
    get_turkey_timezone,
)
from src.utils.team_utils import normalize_text, is_besiktas_team

st.set_page_config(page_title="SEG_Maçkolik", page_icon="⚽", layout="wide")

# --- Turuncu tema (tek satır CSS kuralları, style bloğu girintisiz) ---
st.markdown(
    "<style>"
    ".stApp{background-color:#fff7ed;}"
    'section[data-testid="stSidebar"]{background:linear-gradient(180deg,#431407 0%,#7c2d12 100%);}'
    'section[data-testid="stSidebar"] p,section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] span,section[data-testid="stSidebar"] h1,section[data-testid="stSidebar"] h2,section[data-testid="stSidebar"] h3{color:#ffedd5 !important;}'
    'section[data-testid="stSidebar"] input{color:#431407 !important;-webkit-text-fill-color:#431407 !important;}'
    'section[data-testid="stSidebar"] div[data-baseweb="select"] div{color:#431407 !important;}'
    "h1,h2,h3{color:#9a3412 !important;}"
    ".seg-banner-title{color:#ffffff !important;font-size:2.1rem;font-weight:800;margin:0;}"
    ".seg-section{font-size:15px;font-weight:800;color:#ffffff !important;background:linear-gradient(90deg,#9a3412,#c2410c);border-radius:8px;padding:8px 14px;margin:18px 0 10px 0;}"
    ".seg-date{font-size:13px;font-weight:800;color:#9a3412;margin:14px 0 8px 0;border-bottom:2px solid #fed7aa;padding-bottom:4px;}"
    ".seg-card{background:#ffffff;border:1px solid #fed7aa;border-radius:10px;padding:12px 16px;margin-bottom:10px;}"
    ".seg-card-bjk{background:#fffdf2;border:2px solid #d4af37;border-radius:10px;padding:12px 16px;margin-bottom:10px;box-shadow:0 2px 8px rgba(212,175,55,.25);}"
    ".seg-score{background:#c2410c;color:#fff;border-radius:6px;padding:3px 12px;margin:0 8px;font-weight:700;white-space:nowrap;}"
    ".seg-live{background:#b91c1c;color:#fff;border-radius:6px;padding:3px 10px;margin-right:8px;font-weight:800;animation:segblink 1.2s infinite;}"
    "@keyframes segblink{0%,100%{opacity:1;}50%{opacity:.45;}}"
    ".seg-meta{font-size:12px;color:#9a3412;}"
    ".seg-bjktag{font-size:11px;font-weight:700;color:#b45309;}"
    'div[data-testid="stMetric"]{background:#ffffff;border:1px solid #fed7aa;border-radius:10px;padding:10px;}'
    'div[data-testid="stMetricValue"]{color:#c2410c !important;}'
    'div[data-testid="stMetricLabel"] p{color:#9a3412 !important;font-weight:700;}'
    ".seg-footer{text-align:center;color:#9a3412;font-size:12px;margin-top:26px;}"
    "</style>",
    unsafe_allow_html=True,
)


def logo_data_uri() -> str:
    svg_path = Path(__file__).parent / "assets" / "besiktas.svg"
    return "data:image/svg+xml;base64," + base64.b64encode(svg_path.read_bytes()).decode()


# --- Başlık bandı ---
col_title, col_logo = st.columns([9, 1])
with col_title:
    st.markdown(
        '<div style="background:linear-gradient(135deg,#7c2d12 0%,#ea580c 100%);padding:18px 24px;border-radius:12px;">'
        '<div class="seg-banner-title">SEG_Maçkolik</div>'
        '<div style="color:#ffffff;margin:4px 0 0 0;">Türkiye Süper Lig + Basketbol Süper Ligi • Sonuçlar, Puan Durumu, Fikstür, Gol Krallığı</div>'
        "</div>",
        unsafe_allow_html=True,
    )
with col_logo:
    st.markdown(f'<img src="{logo_data_uri()}" style="width:80px;float:right;" alt="Beşiktaş">', unsafe_allow_html=True)


def monday_of_week(base: datetime) -> datetime:
    return base - timedelta(days=base.weekday())


def build_week_options(n_weeks: int = 10):
    now_tr = datetime.now(get_turkey_timezone())
    options = []
    end_today = now_tr.strftime("%Y-%m-%d")
    start_7 = (now_tr - timedelta(days=6)).strftime("%Y-%m-%d")
    options.append((f"Son 7 gün ({format_date_dots(start_7)} - {format_date_dots(end_today)})", start_7, end_today))
    monday = monday_of_week(now_tr)
    for i in range(n_weeks):
        ws = monday - timedelta(weeks=i)
        we = min(ws + timedelta(days=6), now_tr)
        s, e = ws.strftime("%Y-%m-%d"), we.strftime("%Y-%m-%d")
        options.append((f"{format_report_date(s)} - {format_report_date(e)}", s, e))
    return options


def date_list_between(start_date: str, end_date: str):
    d0 = datetime.strptime(start_date, "%Y-%m-%d")
    d1 = datetime.strptime(end_date, "%Y-%m-%d")
    out, d = [], d0
    while d <= d1:
        out.append(d.strftime("%Y-%m-%d"))
        d += timedelta(days=1)
    return out


@st.cache_data(ttl=3600, show_spinner=False)
def load_results(start_date: str, end_date: str):
    fb, bb = [], []
    for day in date_list_between(start_date, end_date):
        try:
            fb.extend([m for m in football_service.fetch_matches_for_date(day) if m.is_finished])
        except Exception:
            pass
        try:
            bb.extend([m for m in basketball_service.fetch_matches_for_date(day) if m.is_finished])
        except Exception:
            pass
    seen = set()
    uniq_fb = [m for m in fb if not (m.match_id in seen or seen.add(m.match_id))]
    seen.clear()
    uniq_bb = [m for m in bb if not (m.match_id in seen or seen.add(m.match_id))]
    return [
        {"sport": m.sport, "league": m.league, "home": m.home_team, "away": m.away_team,
         "hs": m.home_score or "-", "aws": m.away_score or "-", "date": m.match_date,
         "time": m.start_time, "bjk": m.is_besiktas_match}
        for m in sorted(uniq_fb + uniq_bb, key=lambda x: (x.match_date, x.start_time))
    ]


@st.cache_data(ttl=3600, show_spinner=False)
def load_fixtures():
    """Son 2 gün + yıl sonuna (31 Aralık) kadar oynanmamış (upcoming/live) maçlar. Paralel çekilir."""
    from concurrent.futures import ThreadPoolExecutor
    now_tr = datetime.now(get_turkey_timezone())
    start = (now_tr - timedelta(days=2)).strftime("%Y-%m-%d")
    end = f"{now_tr.year}-12-31"
    days = date_list_between(start, end)
    jobs = [(d, "football") for d in days] + [(d, "basketball") for d in days]

    def _fetch(job):
        day, sport = job
        svc = football_service if sport == "football" else basketball_service
        try:
            day_matches = svc.fetch_matches_for_date(day)
        except Exception:
            return []
        return [(sport, m) for m in day_matches if m.status.strip().lower() in ("upcoming", "live", "halftime")]

    out = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for found in pool.map(_fetch, jobs):
            for sport, m in found:
                out.append({"sport": sport, "league": m.league, "home": m.home_team, "away": m.away_team,
                            "hs": m.home_score or "-", "aws": m.away_score or "-", "date": m.match_date,
                            "time": m.start_time, "status": m.status.strip().lower(),
                            "status_text": m.status_text, "bjk": m.is_besiktas_match})
    seen, uniq = set(), []
    for m in sorted(out, key=lambda x: (x["date"], x["time"])):
        key = (m["home"], m["away"], m["date"])
        if key not in seen:
            seen.add(key)
            uniq.append(m)
    return uniq


@st.cache_data(ttl=3600, show_spinner=False)
def load_standings():
    return standings_service.fetch_football_standings()


@st.cache_data(ttl=3600, show_spinner=False)
def load_scorers(stat_type: str):
    return scorers_service.fetch_top_scorers(stat_type=stat_type, limit=20)


def match_card(m, show_score=True):
    cls = "seg-card-bjk" if m["bjk"] else "seg-card"
    tag = '<div class="seg-bjktag">⭐ BEŞİKTAŞ MAÇI</div>' if m["bjk"] else ""
    icon = "⚽" if m["sport"] == "football" else "🏀"
    live = ""
    if m.get("status") == "live":
        live = f'<span class="seg-live">CANLI • {m.get("status_text", "")}</span>'
    try:
        when = format_date_dots(m["date"]) + (f' {m["time"]}' if m["time"] else "")
        badge_when = when
    except Exception:
        when = m["date"]
        badge_when = m["date"]
    score = f'<span class="seg-score">{m["hs"]} - {m["aws"]}</span>' if show_score else f'<span class="seg-score">{badge_when}</span>'
    return (
        f'<div class="{cls}">{tag}'
        f'<div style="font-size:15px;color:#431407;">{live}<b>{icon} {m["home"]}</b>{score}<b>{m["away"]}</b></div>'
        f'<div class="seg-meta">{m["league"]} • {when}</div>'
        "</div>"
    )


def bjk_star(name: str) -> str:
    """Beşiktaş ise başına yıldız koyar, yazı stili aynı kalır."""
    return f"⭐ {name}" if is_besiktas_team(name) else name


# --- Sayfa seçimi ---
PAGES = {"sonuclar": "Maç Sonuçları", "puan": "Puan Durumu", "fikstur": "Fikstür", "krallik": "Gol Krallığı"}
qp = st.query_params
page = qp.get("page", "sonuclar")
if page not in PAGES:
    page = "sonuclar"

with st.sidebar:
    st.header("Sayfalar")
    choice = st.radio("Bölüm", list(PAGES.values()), index=list(PAGES.keys()).index(page))
    page = {v: k for k, v in PAGES.items()}[choice]
    st.divider()

st.query_params.update({"page": page})

if page == "sonuclar":
    week_options = build_week_options()
    labels = [o[0] for o in week_options]
    default_idx = 0
    if qp.get("start") and qp.get("end"):
        for i, (_, s, e) in enumerate(week_options):
            if s == qp.get("start") and e == qp.get("end"):
                default_idx = i
                break
    with st.sidebar:
        st.header("Filtreler")
        week_label = st.selectbox("Hafta", labels, index=default_idx)
        sel = week_options[labels.index(week_label)]
        start_date, end_date = sel[1], sel[2]
        lig = st.radio("Lig", ["Tümü", "Futbol", "Basketbol"],
                       index={"all": 0, "football": 1, "basketball": 2}.get(qp.get("lig", "all"), 0))
        team_q = st.text_input("Takım ara", value=qp.get("q", ""))
        only_bjk = st.checkbox("Sadece Beşiktaş maçları", value=qp.get("bjk", "") == "1")
        view = st.radio("Görünüm", ["Kartlar", "Tablo"], horizontal=True)
    st.query_params.update({"start": start_date, "end": end_date,
                            "lig": {"Tümü": "all", "Futbol": "football", "Basketbol": "basketball"}[lig],
                            "q": team_q, "bjk": "1" if only_bjk else ""})
    with st.spinner("Maçlar yükleniyor..."):
        matches = load_results(start_date, end_date)
    norm_q = normalize_text(team_q)
    filtered = [m for m in matches
                if (lig == "Tümü" or (lig == "Futbol" and m["sport"] == "football") or (lig == "Basketbol" and m["sport"] == "basketball"))
                and (not only_bjk or m["bjk"])
                and (not norm_q or norm_q in normalize_text(m["home"] + " " + m["away"]))]
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam maç", len(filtered))
    c2.metric("Beşiktaş maçı", sum(1 for m in filtered if m["bjk"]))
    c3.metric("Aralık", f"{format_date_dots(start_date)} - {format_date_dots(end_date)}")
    share_url = f"{settings.app_url.rstrip('/')}/?page=sonuclar&start={start_date}&end={end_date}&lig={qp.get('lig', 'all')}&q={team_q}"
    st.info(f"Bu görünümün linki: {share_url}")
    if view == "Kartlar":
        last_date = None
        for m in filtered:
            if m["date"] != last_date:
                try:
                    readable = format_report_date(m["date"])
                except Exception:
                    readable = m["date"]
                st.markdown(f'<div class="seg-date">📅 {readable}</div>', unsafe_allow_html=True)
                last_date = m["date"]
            st.markdown(match_card(m), unsafe_allow_html=True)
    else:
        df = pd.DataFrame([{"Tarih": m["date"], "Ev Sahibi": m["home"], "Skor": f'{m["hs"]} - {m["aws"]}',
                            "Deplasman": m["away"], "Lig": m["league"],
                            "Beşiktaş": "⭐" if m["bjk"] else ""} for m in filtered])
        st.dataframe(df, use_container_width=True, hide_index=True)
    if not filtered:
        st.warning("Bu filtrelerle eşleşen maç bulunamadı.")

elif page == "puan":
    st.markdown('<div class="seg-section">⚽ Süper Lig Puan Durumu</div>', unsafe_allow_html=True)
    with st.spinner("Puan durumu yükleniyor..."):
        try:
            rows, meta = load_standings()
        except Exception as e:
            st.error(f"Puan durumu alınamadı: {e}")
            rows, meta = [], {}
    if meta.get("competition_logo"):
        st.image(meta["competition_logo"], width=60)
    if rows:
        df = pd.DataFrame([{"S": r["pos"], "Logo": r["team_logo"], "Takım": bjk_star(r["team"]), "O": r["p"],
                            "G": r["w"], "B": r["d"], "M": r["l"], "AV": r["gd"],
                            "Puan": r["pts"], "Not": (r["promo_name"] or "")} for r in rows])
        st.dataframe(df, use_container_width=True, hide_index=True, height=38 * (len(df) + 1),
                     column_config={"Logo": st.column_config.ImageColumn("Logo", width="small"),
                                    "Puan": st.column_config.NumberColumn("Puan", format="%d")})
        bjk = next((r for r in rows if is_besiktas_team(r["team"])), None)
        if bjk:
            st.success(f'Beşiktaş: {bjk["pos"]}. sıra • {bjk["pts"]} puan ({bjk["w"]}G {bjk["d"]}B {bjk["l"]}M, AV {bjk["gd"]})')
    st.markdown('<div class="seg-section">🏀 Basketbol Süper Ligi</div>', unsafe_allow_html=True)
    st.info("SportScore API basketbol puan durumu sunmuyor, bu bölüm yalnızca futbol içindir.")

elif page == "fikstur":
    with st.sidebar:
        st.header("Filtreler")
        f_lig = st.radio("Lig", ["Tümü", "Futbol", "Basketbol"])
        f_q = st.text_input("Takım ara", value="")
        f_bjk = st.checkbox("Sadece Beşiktaş maçları")
    with st.spinner("Fikstür yükleniyor (yıl sonuna kadar taranıyor, ilk açılış 1-2 dk sürebilir)..."):
        fixtures = load_fixtures()
    norm_q = normalize_text(f_q)
    filtered = [m for m in fixtures
                if (f_lig == "Tümü" or (f_lig == "Futbol" and m["sport"] == "football") or (f_lig == "Basketbol" and m["sport"] == "basketball"))
                and (not f_bjk or m["bjk"])
                and (not norm_q or norm_q in normalize_text(m["home"] + " " + m["away"]))]
    live_n = sum(1 for m in filtered if m.get("status") == "live")
    c1, c2 = st.columns(2)
    c1.metric("Yaklaşan / canlı maç", len(filtered))
    c2.metric("Şu an canlı", live_n)
    last_date = None
    for m in filtered:
        if m["date"] != last_date:
            try:
                readable = format_report_date(m["date"])
            except Exception:
                readable = m["date"]
            st.markdown(f'<div class="seg-date">📅 {readable}</div>', unsafe_allow_html=True)
            last_date = m["date"]
        st.markdown(match_card(m, show_score=(m.get("status") == "live")), unsafe_allow_html=True)
    if not filtered:
        st.warning("Taranan aralıkta yaklaşan maç bulunamadı.")

else:  # krallik
    with st.sidebar:
        st.header("Filtreler")
        stat = st.radio("Sıralama", ["Gol", "Asist"], horizontal=True)
    stat_type = "goals" if stat == "Gol" else "assists"
    st.markdown(f'<div class="seg-section">👟 Süper Lig {"Gol" if stat == "Gol" else "Asist"} Krallığı (ilk 20)</div>', unsafe_allow_html=True)
    with st.spinner("Gol krallığı yükleniyor..."):
        try:
            scorers = load_scorers(stat_type)
        except Exception as e:
            st.error(f"Gol krallığı alınamadı: {e}")
            scorers = []
    if scorers:
        df = pd.DataFrame([{"S": s["rank"], "Oyuncu": s["player_logo"], "İsim": s["player"],
                            "Takım Logo": s["team_logo"], "Takım": bjk_star(s["team"]), "Gol": s["goals"],
                            "Asist": s["assists"], "Maç": s["matches"]} for s in scorers])
        st.dataframe(df, use_container_width=True, hide_index=True, height=38 * (len(df) + 1),
                     column_config={"Oyuncu": st.column_config.ImageColumn("Foto", width="small"),
                                    "Takım Logo": st.column_config.ImageColumn("Logo", width="small")})
        top = scorers[0]
        unit = "gol" if stat == "Gol" else "asist"
        val = top["goals"] if stat == "Gol" else top["assists"]
        st.success(f'Lider: {top["player"]} ({top["team"]}) • {val} {unit}')

st.markdown(f'<div class="seg-footer">Veri kaynağı: SportScore • Son güncelleme: {datetime.now(get_turkey_timezone()).strftime("%H:%M")}</div>', unsafe_allow_html=True)
