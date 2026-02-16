import streamlit as st
import json

DATA_FILE = "diagnosis.json"

st.set_page_config(page_title="性格診断", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Noto+Sans+JP:wght@400;700&display=swap');
body { font-family: 'Inter', 'Noto Sans JP', sans-serif; background-color: #f4f6f9; color: #333; }
.stApp { background-color: #f4f6f9; }
.main-title { font-size: 1.8em; font-weight: 800; text-align: center; color: #222; margin-bottom: 30px; }
.result-card { background: #fff; border: none; padding: 40px; border-radius: 16px; margin-top: 40px; text-align: left; box-shadow: 0 10px 30px rgba(0,0,0,0.06); }
.type-label { font-size: 0.75em; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px; }
.type-name { font-size: 2.4em; font-weight: 800; color: #111; margin-bottom: 8px; line-height: 1.2; }
.subtitle { font-size: 1.0em; color: #666; font-weight: 500; margin-bottom: 30px; border-bottom: 1px solid #eee; padding-bottom: 20px; }
.desc-text { font-size: 0.95em; line-height: 1.9; color: #333; margin-top: 30px; white-space: pre-wrap; }
.manual-box { margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #ccc; }
.manual-head { font-size: 0.8em; font-weight: 700; color: #444; display: block; margin-bottom: 6px; }
.tag { display: inline-block; background: #eee; color: #444; padding: 4px 12px; border-radius: 20px; font-size: 0.75em; font-weight: 600; margin-right: 6px; margin-bottom: 6px; }
.scale-container { margin-bottom: 20px; }
.scale-labels { display: flex; justify-content: space-between; font-size: 0.75em; font-weight: 600; color: #666; margin-bottom: 6px; }
.scale-track { height: 6px; background: #e0e0e0; position: relative; margin-top: 6px; border-radius: 3px; }
.scale-marker { position: absolute; top: 50%; transform: translate(-50%, -50%); width: 14px; height: 14px; background: #333; border: 2px solid #fff; border-radius: 50%; box-shadow: 0 1px 3px rgba(0,0,0,0.2); transition: left 0.4s cubic-bezier(0.2, 0.8, 0.2, 1); }
.q-text-style { font-size: 1.15em; font-weight: 700; color: #222; margin-bottom: 15px; line-height: 1.5; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return None

data = load_data()
if not data:
    st.error(f"エラー: {DATA_FILE} が見つかりません。")
    st.stop()

st.markdown(f'<div class="main-title">{data.get("theme", "性格診断")}</div>', unsafe_allow_html=True)

if "answers" not in st.session_state: st.session_state.answers = {}
if "show_result" not in st.session_state: st.session_state.show_result = False

total_q = len(data["questions"])

if not st.session_state.show_result:
    current = len(st.session_state.answers)
    st.progress(min(current / total_q, 1.0))
    st.caption(f"回答状況: {current} / {total_q} 問")

    for i, q in enumerate(data["questions"]):
        with st.container(border=True):
            st.markdown(f'<div class="q-text-style">Q{i+1}. {q["q"]}</div>', unsafe_allow_html=True)
            
            if q.get("swap_options", False):
                t1, t2 = q['option_b'], q['option_a']
            else:
                t1, t2 = q['option_a'], q['option_b']

            val = st.radio(
                f"radio_{i}", 
                [f"A: {t1}", f"B: {t2}"], 
                key=f"q_{i}", 
                index=None,
                label_visibility="collapsed"
            )
            if val: st.session_state.answers[i] = val

    if len(st.session_state.answers) == total_q:
        if st.button("診断結果を見る", type="primary", use_container_width=True):
            st.session_state.show_result = True
            st.rerun()

else:
    scores = [0] * len(data["axes"])
    max_scores = [0] * len(data["axes"])
    
    for i, q in enumerate(data["questions"]):
        val = st.session_state.answers.get(i)
        if val:
            idx = int(q.get("axis_index", 0))
            w = q.get("weight", 1)
            flip = 1 if q.get("swap_options", False) else -1
            delta = flip * w if val.startswith("A:") else -1 * flip * w
            
            if idx < len(scores):
                scores[idx] += delta
                max_scores[idx] += abs(w)

    key_parts = ["1" if s >= 0 else "-1" for s in scores]
    key = ",".join(key_parts)
    res = data["results"].get(key, list(data["results"].values())[0])

    meters_html = ""
    for i, axis in enumerate(data["axes"]):
        cur = scores[i]
        mx = max_scores[i] if max_scores[i] > 0 else 1
        pct = int(((cur + mx) / (2 * mx)) * 100)
        ls = "color:#222;" if pct < 50 else "color:#ccc;"
        rs = "color:#222;" if pct > 50 else "color:#ccc;"
        
        meters_html += f"""<div class="scale-container"><div class="scale-labels"><span style="{ls}">{axis['label_left']}</span><span style="{rs}">{axis['label_right']}</span></div><div class="scale-track"><div class="scale-marker" style="left: {pct}%;"></div></div></div>"""

    tags_html = ' '.join([f'<span class="tag">#{t.replace("#", "")}</span>' for t in res.get('tags', [])])
    gm = res.get('good_match', 'ー')
    bm = res.get('bad_match', 'ー')

    st.markdown(f"""<div class="result-card"><div class="type-label">DIAGNOSIS RESULT</div><div class="type-name">{res['name']}</div><div class="subtitle">{res['subtitle']}</div><div style="margin-bottom:30px;">{tags_html}</div>{meters_html}<div class="desc-text">{res['desc']}</div><div class="manual-box"><span class="manual-head">取扱説明書</span><div style="font-size:0.9em; line-height:1.7; color:#555;">{res['manual']}</div></div><div style="margin-top:30px; font-size:0.8em; color:#888; display:flex; gap:30px;"><div>💖 BEST: <b style="color:#555;">{gm}</b></div><div>💔 WORST: <b style="color:#555;">{bm}</b></div></div></div>""", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📚 他のタイプ図鑑")
    unique_res = {}
    for v in data["results"].values():
        if v["name"] not in unique_res: unique_res[v["name"]] = v
    
    for name, info in unique_res.items():
        lt = f"▼ 【{info['name']}】 : {info['subtitle']}"
        with st.expander(lt):
            st.markdown(f"""<div style="padding:10px;"><div style="margin-bottom:10px;">{' '.join([f'<span class="tag">#{t.replace("#", "")}</span>' for t in info.get('tags', [])])}</div><div class="desc-text" style="margin-top:0;">{info['desc']}</div><div class="manual-box" style="margin-top:15px;"><span class="manual-head">取扱説明書</span><div style="font-size:0.9em; color:#555;">{info['manual']}</div></div></div>""", unsafe_allow_html=True)
    
    st.markdown("---")
    if st.button("もう一度診断する", use_container_width=True):
        st.session_state.answers = {}
        st.session_state.show_result = False
        st.rerun()
