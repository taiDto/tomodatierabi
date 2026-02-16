import streamlit as st
import json

# --- 設定 ---
DATA_FILE = "diagnosis.json"

st.set_page_config(page_title="性格診断", layout="centered")

# --- CSSデザイン（カードデザイン・文字サイズ調整） ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Noto+Sans+JP:wght@400;700&display=swap');
    
    /* 全体の背景とフォント */
    body { font-family: 'Inter', 'Noto Sans JP', sans-serif; background-color: #f4f6f9; color: #333; }
    .stApp { background-color: #f4f6f9; }
    
    /* タイトル */
    .main-title { font-size: 2.0em; font-weight: 800; text-align: center; color: #222; margin-bottom: 30px; }
    
    /* 質問カード内のテキスト */
    .q-text { font-size: 1.2em; font-weight: 700; color: #111; margin-bottom: 15px; line-height: 1.5; }
    
    /* 選択肢（ラジオボタン）のスタイル調整 */
    .stRadio > div { gap: 10px; }
    
    /* 結果カード */
    .result-card { background: #fff; padding: 40px; border-radius: 16px; margin-top: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .type-name { font-size: 2.4em; font-weight: 800; color: #111; margin-bottom: 10px; line-height: 1.2; }
    .subtitle { font-size: 1.1em; color: #666; font-weight: 500; margin-bottom: 25px; border-bottom: 1px solid #eee; padding-bottom: 20px; }
    .desc-text { font-size: 1.0em; line-height: 1.8; color: #333; white-space: pre-wrap; margin-top: 20px; }
    
    /* パラメータ（棒グラフ） */
    .scale-container { margin-bottom: 15px; }
    .scale-labels { display: flex; justify-content: space-between; font-size: 0.8em; font-weight: 600; color: #555; margin-bottom: 5px; }
    .scale-track { height: 8px; background: #e0e0e0; position: relative; border-radius: 4px; overflow: hidden; }
    .scale-bar { height: 100%; background: #333; border-radius: 4px; }
    
    /* 取扱説明書ボックス */
    .manual-box { margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #ccc; }
    
    /* タグ */
    .tag { display: inline-block; background: #eee; color: #444; padding: 5px 12px; border-radius: 20px; font-size: 0.8em; font-weight: 600; margin-right: 5px; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# データの読み込み
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

# --- 質問フェーズ ---
if not st.session_state.show_result:
    total_q = len(data["questions"])
    current_val = len(st.session_state.answers)
    st.progress(current_val / total_q)
    st.caption(f"進捗: {current_val} / {total_q} 問")

    for i, q in enumerate(data["questions"]):
        # ★ここが修正点：st.container(border=True) で「枠」を作って、その中に質問とボタンを入れる
        with st.container(border=True):
            st.markdown(f'<div class="q-text">Q{i+1}. {q["q"]}</div>', unsafe_allow_html=True)
            
            # 選択肢の表示ロジック
            opt_a = q['option_b'] if q.get("swap_options") else q['option_a']
            opt_b = q['option_a'] if q.get("swap_options") else q['option_b']
            
            val = st.radio(
                f"radio_{i}", 
                [f"A: {opt_a}", f"B: {opt_b}"], 
                index=None, 
                key=f"q_{i}",
                label_visibility="collapsed" # ラベル重複回避
            )
            if val: st.session_state.answers[i] = val

    # 全問回答したらボタン表示
    if len(st.session_state.answers) == total_q:
        if st.button("診断結果を見る", type="primary", use_container_width=True):
            st.session_state.show_result = True
            st.rerun()

# --- 結果フェーズ ---
else:
    # スコア計算
    scores = [0] * len(data["axes"])
    max_scores = [0] * len(data["axes"])
    for i, q in enumerate(data["questions"]):
        val = st.session_state.answers.get(i)
        if val:
            idx = int(q.get("axis_index", 0))
            weight = q.get("weight", 1)
            # A選択ならプラス、Bならマイナス（swap考慮済み）
            point = weight if val.startswith("A:") else -weight
            
            if idx < len(scores):
                scores[idx] += point
                max_scores[idx] += abs(weight)

    # 結果タイプの判定
    key = ",".join(["1" if s >= 0 else "-1" for s in scores])
    res = data["results"].get(key, list(data["results"].values())[0])

    # --- HTML生成（パラメータバー復活） ---
    meters_html = ""
    for i, axis in enumerate(data["axes"]):
        current = scores[i]
        maximum = max_scores[i] if max_scores[i] > 0 else 1
        # -Max ~ +Max を 0% ~ 100% に変換
        percent = int(((current + maximum) / (2 * maximum)) * 100)
        
        meters_html += f"""
        <div class="scale-container">
            <div class="scale-labels">
                <span>{axis['label_left']}</span>
                <span>{axis['label_right']}</span>
            </div>
            <div class="scale-track">
                <div class="scale-bar" style="width: {percent}%; background: {'#333' if percent > 50 else '#999'};"></div>
            </div>
        </div>
        """

    tags = ' '.join([f'<span class="tag">#{t}</span>' for t in res.get('tags', [])])
    
    st.markdown(f"""
    <div class="result-card">
        <div style="font-size:0.8em; color:#888; margin-bottom:5px;">DIAGNOSIS RESULT</div>
        <div class="type-name">{res['name']}</div>
        <div class="subtitle">{res['subtitle']}</div>
        <div style="margin-bottom:25px;">{tags}</div>
        
        <div style="background:#f9f9f9; padding:15px; border-radius:8px; margin-bottom:20px;">
            {meters_html}
        </div>

        <div class="desc-text">{res['desc']}</div>
        
        <div class="manual-box">
            <div style="font-weight:bold; margin-bottom:5px;">取扱説明書</div>
            <div style="font-size:0.9em; color:#555;">{res['manual']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # --- 図鑑機能（復活） ---
    st.markdown("---")
    st.subheader("📚 他のタイプ図鑑")
    unique_res = {}
    for v in data["results"].values():
        if v["name"] not in unique_res: unique_res[v["name"]] = v
        
    for name, info in unique_res.items():
        with st.expander(f"▼ {name} : {info['subtitle']}"):
            st.markdown(f"**{info['desc'][:50]}...**")
            st.write(info['desc'])

    st.markdown("---")
    if st.button("もう一度診断する", use_container_width=True):
        st.session_state.answers = {}
        st.session_state.show_result = False
        st.rerun()
