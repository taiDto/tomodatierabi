import streamlit as st
import json

# --- 設定 ---
DATA_FILE = "diagnosis.json"

st.set_page_config(page_title="性格診断", layout="centered")

# CSS（デザイン修正版：選択肢も枠に入れる）
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Noto+Sans+JP:wght@400;700&display=swap');
    body { font-family: 'Inter', 'Noto Sans JP', sans-serif; background-color: #f4f6f9; color: #333; }
    .stApp { background-color: #f4f6f9; }
    .main-title { font-size: 1.8em; font-weight: 800; text-align: center; color: #222; margin-bottom: 30px; }
    
    /* 質問と選択肢をセットで包む白いカード */
    .question-card { 
        background-color: #ffffff; 
        padding: 24px; 
        border-radius: 16px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); 
        margin-bottom: 24px; 
        border: 1px solid #eee; 
    }
    
    .q-text-style { font-size: 1.1em; font-weight: 700; color: #222; margin-bottom: 20px; line-height: 1.5; }
    
    /* ラジオボタン自体の余白調整 */
    div[data-testid="stRadio"] > label { display: none; } /* 不要なラベルを隠す */
    
    /* 結果カード */
    .result-card { background: #fff; padding: 40px; border-radius: 20px; margin-top: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.06); }
    .type-name { font-size: 2.2em; font-weight: 800; color: #111; margin-bottom: 8px; }
    .subtitle { color: #666; font-weight: 500; margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 20px; }
    .desc-text { line-height: 1.8; color: #333; white-space: pre-wrap; }
    .manual-box { margin-top: 25px; padding: 20px; background: #f8f9fa; border-radius: 10px; border-left: 5px solid #ddd; }
    .tag { display: inline-block; background: #eee; color: #444; padding: 4px 12px; border-radius: 20px; font-size: 0.75em; font-weight: 600; margin-right: 6px; }
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
    st.error("JSONファイルが見つかりません。")
    st.stop()

st.markdown(f'<div class="main-title">{data.get("theme", "性格診断")}</div>', unsafe_allow_html=True)

if "answers" not in st.session_state: st.session_state.answers = {}
if "show_result" not in st.session_state: st.session_state.show_result = False

# --- 質問フェーズ ---
if not st.session_state.show_result:
    total_q = len(data["questions"])
    st.progress(len(st.session_state.answers) / total_q)

    for i, q in enumerate(data["questions"]):
        # ここで「質問文」と「選択肢」を一つの div で囲む
        st.markdown(f'<div class="question-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="q-text-style">Q{i+1}. {q["q"]}</div>', unsafe_allow_html=True)
        
        # 選択肢の準備
        opt_a = q['option_b'] if q.get("swap_options") else q['option_a']
        opt_b = q['option_a'] if q.get("swap_options") else q['option_b']
        
        # ラジオボタン
        val = st.radio(
            f"q_{i}", 
            [f"A: {opt_a}", f"B: {opt_b}"], 
            index=None, 
            key=f"radio_{i}",
            horizontal=False # 縦並びの方がカード内に収まりがいいです
        )
        if val: st.session_state.answers[i] = val
        
        st.markdown('</div>', unsafe_allow_html=True)

    if len(st.session_state.answers) == total_q:
        if st.button("診断結果を見る", type="primary", use_container_width=True):
            st.session_state.show_result = True
            st.rerun()

# --- 結果フェーズ（省略せず図鑑機能付き） ---
else:
    # スコア計算
    scores = [0] * len(data["axes"])
    max_scores = [1] * len(data["axes"])
    for i, q in enumerate(data["questions"]):
        val = st.session_state.answers.get(i)
        if val:
            idx = int(q.get("axis_index", 0))
            weight = q.get("weight", 1)
            # Aならプラス、Bならマイナスの簡易ロジック
            score_delta = weight if val.startswith("A:") else -weight
            if idx < len(scores): scores[idx] += score_delta

    key = ",".join(["1" if s >= 0 else "-1" for s in scores])
    res = data["results"].get(key, list(data["results"].values())[0])

    # 結果表示（HTML）
    tags_html = ' '.join([f'<span class="tag">#{t}</span>' for t in res.get('tags', [])])
    st.markdown(f"""
    <div class="result-card">
        <div class="type-name">{res['name']}</div>
        <div class="subtitle">{res['subtitle']}</div>
        <div style="margin-bottom:20px;">{tags_html}</div>
        <div class="desc-text">{res['desc']}</div>
        <div class="manual-box">
            <div style="font-weight:bold; font-size:0.8em; color:#888;">取扱説明書</div>
            <div style="font-size:0.9em; color:#444;">{res['manual']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📚 他のタイプ図鑑")
    unique_res = {v["name"]: v for v in data["results"].values()}
    for name, info in unique_res.items():
        with st.expander(f"▼ {name} : {info['subtitle']}"):
            st.write(info['desc'])

    if st.button("もう一度診断する"):
        st.session_state.answers = {}
        st.session_state.show_result = False
        st.rerun()
