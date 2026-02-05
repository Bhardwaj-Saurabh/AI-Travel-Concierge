#!/usr/bin/env python3
"""
Streamlit Chat UI for the AI Travel Concierge
Run with: streamlit run streamlit_app.py
"""

import re
import json
import html as html_lib
import streamlit as st

from app.main import run_request

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="AI Travel Concierge",
    page_icon="✈️",
    layout="centered",
)

# ── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { max-width: 860px; }

    /* ── Header banner ───────────────── */
    .trip-hdr {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        border-radius: 14px;
        padding: 1.5rem 1.8rem;
        margin-bottom: 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 0.5rem;
        border: 1px solid rgba(255,255,255,0.06);
    }
    .trip-hdr .th-dest {
        font-size: 1.35rem;
        font-weight: 700;
        color: #f0f4f8;
        letter-spacing: -0.3px;
    }
    .trip-hdr .th-dates {
        background: rgba(255,255,255,0.12);
        color: #cbd5e1;
        padding: 0.28rem 0.85rem;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .trip-hdr .th-badge {
        background: rgba(52,211,153,0.15);
        color: #6ee7b7;
        padding: 0.22rem 0.7rem;
        border-radius: 20px;
        font-size: 0.68rem;
        font-weight: 600;
        letter-spacing: 0.3px;
    }

    /* ── Section wrapper ─────────────── */
    .sec {
        background: rgba(255,255,255,0.025);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 10px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.75rem;
    }
    .sec-hd {
        display: flex;
        align-items: center;
        gap: 0.45rem;
        margin-bottom: 0.7rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    .sec-hd .sec-icon { font-size: 1.1rem; }
    .sec-hd .sec-label {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: rgba(255,255,255,0.45);
    }

    /* ── Metric grid (weather, currency) ── */
    .m-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 0.5rem;
    }
    .m-cell {
        background: rgba(255,255,255,0.04);
        border-radius: 8px;
        padding: 0.75rem 0.6rem;
        text-align: center;
    }
    .m-cell .m-val {
        font-size: 1.2rem;
        font-weight: 700;
        color: #e2e8f0;
    }
    .m-cell .m-lbl {
        font-size: 0.6rem;
        color: rgba(255,255,255,0.35);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 0.15rem;
    }
    /* Accent variant for currency */
    .m-cell.accent {
        background: rgba(251,191,36,0.06);
        border: 1px solid rgba(251,191,36,0.1);
    }
    .m-cell.accent .m-val { color: #fbbf24; }

    /* ── Credit card widget ──────────── */
    .cc-box {
        background: linear-gradient(145deg, #1e1b4b, #312e81);
        border: 1px solid rgba(129,140,248,0.15);
        border-radius: 12px;
        padding: 1.2rem 1.3rem;
        position: relative;
        overflow: hidden;
    }
    .cc-box::before {
        content: '';
        position: absolute;
        top: -30px;
        right: -30px;
        width: 100px;
        height: 100px;
        background: rgba(129,140,248,0.08);
        border-radius: 50%;
    }
    .cc-box .cc-type {
        font-size: 0.6rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: rgba(255,255,255,0.35);
        margin-bottom: 0.35rem;
    }
    .cc-box .cc-name {
        font-size: 1.05rem;
        font-weight: 700;
        color: #c4b5fd;
        margin-bottom: 0.7rem;
    }
    .cc-box .cc-row {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
    }
    .cc-box .cc-col .cc-k {
        font-size: 0.58rem;
        color: rgba(255,255,255,0.3);
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }
    .cc-box .cc-col .cc-v {
        font-size: 0.82rem;
        color: #e2e8f0;
        font-weight: 500;
        margin-top: 0.1rem;
    }
    .cc-box .cc-src {
        font-size: 0.65rem;
        color: rgba(255,255,255,0.25);
        margin-top: 0.6rem;
        padding-top: 0.5rem;
        border-top: 1px solid rgba(255,255,255,0.05);
    }

    /* ── Restaurant card ─────────────── */
    .resto {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 8px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.5rem;
        transition: border-color 0.2s, background 0.2s;
    }
    .resto:hover {
        border-color: rgba(129,140,248,0.25);
        background: rgba(255,255,255,0.04);
    }
    .resto .r-top {
        display: flex;
        align-items: center;
        gap: 0.55rem;
    }
    .resto .r-num {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: #fff;
        min-width: 22px;
        height: 22px;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.68rem;
        flex-shrink: 0;
    }
    .resto .r-name {
        font-weight: 600;
        font-size: 0.88rem;
        color: #e2e8f0;
    }
    .resto .r-name a { color: #a5b4fc; text-decoration: none; }
    .resto .r-name a:hover { text-decoration: underline; color: #c4b5fd; }
    .resto .r-desc {
        font-size: 0.78rem;
        color: rgba(255,255,255,0.5);
        line-height: 1.45;
        margin: 0.3rem 0 0 2rem;
    }
    .resto .r-link {
        margin: 0.3rem 0 0 2rem;
    }
    .resto .r-link a {
        font-size: 0.68rem;
        color: #818cf8;
        text-decoration: none;
        opacity: 0.7;
    }
    .resto .r-link a:hover { opacity: 1; text-decoration: underline; }

    /* ── Next steps ───────────────────── */
    .ns-row {
        display: flex;
        align-items: flex-start;
        gap: 0.55rem;
        padding: 0.45rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.03);
    }
    .ns-row:last-child { border-bottom: none; }
    .ns-row .ns-dot {
        background: #34d399;
        color: #064e3b;
        min-width: 20px;
        height: 20px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.6rem;
        font-weight: 700;
        flex-shrink: 0;
        margin-top: 1px;
    }
    .ns-row .ns-txt {
        font-size: 0.82rem;
        color: rgba(255,255,255,0.7);
    }

    /* ── Sources row ──────────────────── */
    .src-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem 0.6rem;
    }
    .src-row a {
        font-size: 0.7rem;
        color: #818cf8;
        text-decoration: none;
        padding: 0.18rem 0.45rem;
        background: rgba(129,140,248,0.07);
        border-radius: 4px;
        transition: background 0.15s;
    }
    .src-row a:hover { background: rgba(129,140,248,0.14); text-decoration: underline; }
    .src-row .src-txt {
        font-size: 0.7rem;
        color: rgba(255,255,255,0.35);
        padding: 0.18rem 0.45rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Session state ────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Title ────────────────────────────────────────────────────
st.title("✈️ AI Travel Concierge")
st.caption("Type your travel plans — e.g. *\"I want to go to Paris from June 1-8 with my BankGold card\"*")


# ── Helpers ──────────────────────────────────────────────────
def esc(text):
    return html_lib.escape(str(text)) if text else ""


def _parse_restaurant_snippet(snippet):
    """Parse the AI agent's restaurant snippet into structured entries."""
    restaurants = []
    current = None

    for raw_line in snippet.split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        # Strip markdown bold markers
        line = line.replace("**", "")

        lower = line.lower()

        # Key-value lines (URL, Description, Source, etc.)
        if re.match(r'^(url|link)\s*:', lower):
            if current:
                val = re.split(r'^(?:url|link)\s*:\s*', line, flags=re.IGNORECASE)
                current["url"] = val[1].strip() if len(val) > 1 else ""
            continue
        if re.match(r'^description\s*:', lower):
            if current:
                val = re.split(r'^description\s*:\s*', line, flags=re.IGNORECASE)
                current["description"] = val[1].strip() if len(val) > 1 else ""
            continue
        if re.match(r'^(source|category)\s*:', lower):
            continue

        # Skip intro/summary lines
        if any(p in lower for p in ["here are", "based on", "top 5", "top five", "according to", "recent expert"]):
            continue

        # Remove citation brackets
        line = re.sub(r'【.*?】', '', line).strip()
        if not line:
            continue

        # Detect numbered restaurant names
        name_match = re.match(r'^\d+[\.\)]\s*(.+)', line)
        if name_match:
            candidate = name_match.group(1).strip()
            if len(candidate) < 120:
                if current:
                    restaurants.append(current)
                current = {"name": candidate, "description": "", "url": ""}
                continue

        # Description line
        if current and not current.get("description"):
            desc = re.sub(r'^-\s*', '', line).strip()
            if desc:
                current["description"] = desc

    if current:
        restaurants.append(current)
    return restaurants if restaurants else []


def build_plan_html(plan):
    """Build styled HTML for the trip plan."""
    parts = []

    dest = esc(plan.get("destination", "Unknown")).title()
    dates = esc(plan.get("travel_dates", "Not specified"))

    # ── Header
    parts.append(
        f'<div class="trip-hdr">'
        f'<div class="th-dest">📍 {dest}</div>'
        f'<div style="display:flex;gap:0.4rem;align-items:center;flex-wrap:wrap;">'
        f'<div class="th-dates">📅 {dates}</div>'
        f'<div class="th-badge">✓ Validated</div>'
        f'</div>'
        f'</div>'
    )

    # ── Weather
    w = plan.get("weather")
    if w:
        temp = w.get("temperature_c", "N/A")
        cond = esc(w.get("conditions", "N/A"))
        rec = esc(w.get("recommendation", ""))
        cells = (
            f'<div class="m-cell"><div class="m-val">{temp}°C</div><div class="m-lbl">Temperature</div></div>'
            f'<div class="m-cell"><div class="m-val">{cond}</div><div class="m-lbl">Conditions</div></div>'
        )
        if rec:
            cells += f'<div class="m-cell"><div class="m-val" style="font-size:0.82rem;">{rec}</div><div class="m-lbl">Tip</div></div>'
        parts.append(
            f'<div class="sec">'
            f'<div class="sec-hd"><span class="sec-icon">🌤️</span><span class="sec-label">Weather</span></div>'
            f'<div class="m-grid">{cells}</div>'
            f'</div>'
        )

    # ── Restaurants / Search Results
    results = plan.get("results") or plan.get("restaurants")
    if results:
        main_result = results[0] if results else None
        link_results = results[1:] if len(results) > 1 else []

        cards_html = ""
        idx = 0

        # Parse the AI-generated snippet from first result
        if main_result:
            snippet = main_result.get("snippet", "").strip()
            if snippet:
                parsed = _parse_restaurant_snippet(snippet)
                for r in parsed:
                    idx += 1
                    name = esc(r["name"])
                    desc = esc(r.get("description", ""))
                    url = r.get("url", "")
                    name_html = f'<a href="{esc(url)}" target="_blank">{name}</a>' if url else name
                    desc_html = f'<div class="r-desc">{desc}</div>' if desc else ""
                    link_html = f'<div class="r-link"><a href="{esc(url)}" target="_blank">Visit website →</a></div>' if url else ""
                    cards_html += (
                        f'<div class="resto">'
                        f'<div class="r-top"><div class="r-num">{idx}</div><div class="r-name">{name_html}</div></div>'
                        f'{desc_html}'
                        f'{link_html}'
                        f'</div>'
                    )

        # Additional link results (deduplicated)
        seen_urls = set()
        for r in link_results:
            title = r.get("title", "").strip()
            url = r.get("url", "")
            if not title or not url:
                continue
            url_key = url.rstrip("/").lower()
            if url_key in seen_urls:
                continue
            seen_urls.add(url_key)
            idx += 1
            domain = url.split("/")[2].replace("www.", "") if "/" in url else ""
            desc_html = f'<div class="r-desc">{esc(domain)}</div>' if domain else ""
            cards_html += (
                f'<div class="resto">'
                f'<div class="r-top"><div class="r-num">{idx}</div>'
                f'<div class="r-name"><a href="{esc(url)}" target="_blank">{esc(title)}</a></div></div>'
                f'{desc_html}'
                f'</div>'
            )

        if cards_html:
            parts.append(
                f'<div class="sec">'
                f'<div class="sec-hd"><span class="sec-icon">🍽️</span><span class="sec-label">Restaurant Recommendations</span></div>'
                f'{cards_html}'
                f'</div>'
            )

    # ── Card recommendation
    cr = plan.get("card_recommendation")
    if cr:
        card_name = esc(cr.get("card", "N/A"))
        benefit = esc(cr.get("benefit", "N/A"))
        fx = esc(cr.get("fx_fee", "N/A"))
        source = cr.get("source", "")
        is_user_card = "Your card" in source
        type_label = "YOUR CARD" if is_user_card else "RECOMMENDED CARD"
        source_html = f'<div class="cc-src">{esc(source)}</div>' if source else ""
        parts.append(
            f'<div class="sec">'
            f'<div class="sec-hd"><span class="sec-icon">💳</span><span class="sec-label">Credit Card</span></div>'
            f'<div class="cc-box">'
            f'<div class="cc-type">{type_label}</div>'
            f'<div class="cc-name">{card_name}</div>'
            f'<div class="cc-row">'
            f'<div class="cc-col"><div class="cc-k">Benefit</div><div class="cc-v">{benefit}</div></div>'
            f'<div class="cc-col" style="text-align:right;"><div class="cc-k">FX Fee</div><div class="cc-v">{fx}</div></div>'
            f'</div>'
            f'{source_html}'
            f'</div></div>'
        )

    # ── Currency
    cur = plan.get("currency_info")
    if cur:
        cells = ""
        if cur.get("usd_to_eur"):
            cells += f'<div class="m-cell accent"><div class="m-val">{cur["usd_to_eur"]}</div><div class="m-lbl">USD → Local</div></div>'
        if cur.get("sample_meal_usd"):
            cells += f'<div class="m-cell accent"><div class="m-val">${cur["sample_meal_usd"]:.0f}</div><div class="m-lbl">Meal (USD)</div></div>'
        if cur.get("sample_meal_eur"):
            cells += f'<div class="m-cell accent"><div class="m-val">€{cur["sample_meal_eur"]:.0f}</div><div class="m-lbl">Meal (Local)</div></div>'
        if cur.get("points_earned"):
            cells += f'<div class="m-cell accent"><div class="m-val">{cur["points_earned"]}</div><div class="m-lbl">Points Earned</div></div>'
        if cells:
            parts.append(
                f'<div class="sec">'
                f'<div class="sec-hd"><span class="sec-icon">💱</span><span class="sec-label">Currency &amp; Spending</span></div>'
                f'<div class="m-grid">{cells}</div>'
                f'</div>'
            )

    # ── Next steps
    steps = plan.get("next_steps")
    if steps:
        rows = ""
        for i, s in enumerate(steps, 1):
            rows += f'<div class="ns-row"><div class="ns-dot">{i}</div><div class="ns-txt">{esc(s)}</div></div>'
        parts.append(
            f'<div class="sec">'
            f'<div class="sec-hd"><span class="sec-icon">📋</span><span class="sec-label">Next Steps</span></div>'
            f'{rows}'
            f'</div>'
        )

    # ── Sources
    cites = plan.get("citations")
    if cites:
        links = ""
        for c in cites[:5]:
            c = c.strip()
            if c.startswith("http"):
                domain = c.split("/")[2] if "/" in c else c
                links += f'<a href="{esc(c)}" target="_blank">{esc(domain)}</a>'
            else:
                links += f'<span class="src-txt">{esc(c)}</span>'
        parts.append(
            f'<div class="sec">'
            f'<div class="sec-hd"><span class="sec-icon">📚</span><span class="sec-label">Sources</span></div>'
            f'<div class="src-row">{links}</div>'
            f'</div>'
        )

    return "\n".join(parts)


# ── Render chat history ──────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("html"):
            st.markdown(msg["html"], unsafe_allow_html=True)
        else:
            st.markdown(msg["content"])

# ── Chat input ───────────────────────────────────────────────
if prompt := st.chat_input("Where do you want to go? e.g. Paris from June 1-8 with my BankGold card"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Planning your trip..."):
            try:
                result = run_request(prompt)
                plan_data = json.loads(result)
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})
                plan_data = None

        if plan_data and "error" in plan_data:
            err = plan_data["error"]
            st.error(err)
            st.session_state.messages.append({"role": "assistant", "content": f"Error: {err}"})
        elif plan_data:
            plan = plan_data.get("plan", plan_data)
            html = build_plan_html(plan)
            st.markdown(html, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "html": html})
