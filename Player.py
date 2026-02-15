import streamlit as st
import json

# --- 設定 ---
# 読み込むJSONファイル名（GitHubのファイル名と完全に一致させること）
DATA_FILE = "diagnosis.json"

st.set_page_config(page_title="性格診断", layout="centered")

# CSS（デザイン）
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Noto+Sans+JP:wght@400;700&display=swap');
    body { font-family: 'Inter', 'Noto Sans JP', sans-serif; background-color: #f4f6f9; color: #333; }
    .stApp { background-color: #f4f6f9; }
    .main-title { font-size: 1.8em; font-weight: 800; text-align: center; color: #222; margin-bottom: 30px; }
    .question-container { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.03); margin-bottom: 20px; border: 1px solid #eee; }
    .q-text-style { font-size: 1.15em; font-weight: 700; color: #222; margin-bottom: 15px; line-height: 1.5; }
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
</style>
""", unsafe_allow_html=True)

# データの読み込み
@st.cache_data
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

data = load_data()

if not data:
    st.error(f"エラー: {DATA_FILE} が見つかりません。同じフォルダに置いてください。")
    st.stop()

st.markdown(f'<div class="main-title">{data.get("theme", "性格診断")}</div>', unsafe_allow_html=True)

# セッション状態の初期化
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "show_result" not in st.session_state:
    st.session_state.show_result = False

total_q = len(data["questions"])
current_answered = len(st.session_state.answers)

# --- まだ結果表示モードでない場合：質問を表示 ---
if not st.session_state.show_result:
    st.progress(min(current_answered / total_q, 1.0))
    st.caption(f"回答状況: {current_answered} / {total_q} 問")

    # 質問ループ
    for i, q in enumerate(data["questions"]):
        with st.container():
            st.markdown(f"""
            <div class="question-container">
                <div class="q-text-style">Q{i+1}. {q["q"]}</div>
            """, unsafe_allow_html=True)
            
            if q.get("swap_options", False):
                text_top = q['option_b'] # 右
                text_bottom = q['option_a'] # 左
            else:
                text_top = q['option_a'] # 左
                text_bottom = q['option_b'] # 右

            display_options = [f"A: {text_top}", f"B: {text_bottom}"]
            
            key_name = f"q_{i}"
            val = st.radio(
                f"label_{i}", 
                display_options, 
                key=key_name, 
                index=None,
                horizontal=True,
                label_visibility="collapsed"
            )
            
            if val:
                st.session_state.answers[i] = val
            
            st.markdown("</div>", unsafe_allow_html=True)

    # 全問回答したら結果ボタンを表示
    if len(st.session_state.answers) == total_q:
        if st.button("診断結果を見る", type="primary"):
            st.session_state.show_result = True
            st.rerun()
    else:
        st.info("全ての質問に回答すると、結果ボタンが表示されます。")

# --- 結果表示モード ---
else:
    # スコア計算
    scores = [0] * len(data["axes"])
    max_scores = [0] * len(data["axes"])
    
    for i, q in enumerate(data["questions"]):
        val = st.session_state.answers.get(i)
        if val:
            idx = int(q.get("axis_index", 0))
            weight = q.get("weight", 1)
            
            # ロジック再現
            if q.get("swap_options", False):
                val_top_score = 1 
            else:
                val_top_score = -1

            if val.startswith("A:"):
                score_delta = val_top_score * weight
            else:
                score_delta = -1 * val_top_score * weight
            
            if idx < len(scores):
                scores[idx] += score_delta
                max_scores[idx] += abs(weight)

    # 結果特定
    key = ",".join(["1" if s >= 0 else "-1" for s in scores])
    res = data["results"].get(key)
    if not res:
         res = list(data["results"].values())[0]

    # 結果描画
    meters_html = ""
    for i, axis in enumerate(data["axes"]):
        current = scores[i]
        maximum = max_scores[i] if max_scores[i] > 0 else 1
        percent = int(((current + maximum) / (2 * maximum)) * 100)
        
        left_style = "color:#222;" if percent < 50 else "color:#ccc;"
        right_style = "color:#222;" if percent > 50 else "color:#ccc;"
        
        meters_html += f"""
        <div class="scale-container">
            <div class="scale-labels">
                <span style="{left_style}">{axis['label_left']}</span>
                <span style="{right_style}">{axis['label_right']}</span>
            </div>
            <div class="scale-track">
                <div class="scale-marker" style="left: {percent}%;"></div>
            </div>
        </div>
        """

    tags_html = ' '.join([f'<span class="tag">#{t.replace("#", "")}</span>' for t in res.get('tags', [])])
    good_match = res.get('good_match', 'ー')
    bad_match = res.get('bad_match', 'ー')

    raw_html = f"""
    <div class="result-card">
        <div class="type-label">DIAGNOSIS RESULT</div>
        <div class="type-name">{res['name']}</div>
        <div class="subtitle">{res['subtitle']}</div>
        <div style="margin-bottom:30px;">{tags_html}</div>
        {meters_html}
        <div class="desc-text">{res['desc']}</div>
        <div class="manual-box">
            <span class="manual-head">取扱説明書</span>
            <div style="font-size:0.9em; line-height:1.7; color:#555;">{res['manual']}</div>
        </div>
        <div style="margin-top:30px; font-size:0.8em; color:#888; display:flex; gap:30px;">
            <div>💖 BEST: <b style="color:#555;">{good_match}</b></div>
            <div>💔 WORST: <b style="color:#555;">{bad_match}</b></div>
        </div>
    </div>
    """
    st.markdown(raw_html.replace("\n", " "), unsafe_allow_html=True)
    
    # --- 追加機能：他のタイプ図鑑 ---
    st.markdown("---")
    st.markdown("### 📚 他のタイプ図鑑")
    unique_results = {}
    for k, v in data["results"].items():
        if v["name"] not in unique_results:
            unique_results[v["name"]] = v
    
    for name, info in unique_results.items():
        label_text = f"▼ 【{info['name']}】 : {info['subtitle']}"
        
        with st.expander(label_text):
            st.markdown(f"""
            <div style="padding:10px;">
                <div style="margin-bottom:10px;">{' '.join([f'<span class="tag">#{t.replace("#", "")}</span>' for t in info.get('tags', [])])}</div>
                <div class="desc-text" style="margin-top:0;">{info['desc']}</div>
                <div class="manual-box" style="margin-top:15px;">
                    <span class="manual-head">取扱説明書</span>
                    <div style="font-size:0.9em; color:#555;">{info['manual']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    if st.button("もう一度診断する"):
        st.session_state.answers = {}
        st.session_state.show_result = False
        st.rerun()