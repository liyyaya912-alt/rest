import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="智慧產線稼動率與異常排查看板",
    page_icon="🏭",
    layout="wide",
)


ALARM_KNOWLEDGE_BASE = {
    "Err-401 馬達過熱": {
        "category": "電氣/控制問題",
        "summary": "馬達溫度超出安全範圍，常見原因包含長時間高負載、散熱不良、風扇異常、軸承阻力過大或驅動器參數設定不當。",
        "checks": [
            "確認機台已停止進料，操作員站位避開旋轉軸與高溫區域，檢查馬達外殼是否有明顯高溫、焦味或異音。",
            "查看控制面板或變頻器/伺服驅動器的負載率與溫度紀錄，確認散熱風扇是否運轉、濾網是否堵塞。",
        ],
        "sop": [
            "按下停止鍵並完成安全確認，必要時執行 LOTO（上鎖掛牌）後再靠近檢查。",
            "清潔馬達散熱孔、風扇與控制箱濾網，排除周邊堆料或遮蔽物。",
            "確認負載機構無卡滯後，於 HMI 清除 Err-401 警報並執行 Reset。",
            "以低速或手動模式試運轉 3 至 5 分鐘，確認電流、溫度與異音均正常後恢復自動生產。",
        ],
        "tpm": "建議將馬達溫度、散熱風扇狀態與控制箱濾網清潔納入每日自主保養點檢表，並設定每週趨勢追蹤，提前發現負載上升或散熱衰退。",
    },
    "Err-302 感應器異常": {
        "category": "電氣/控制問題",
        "summary": "感應器訊號未達預期，可能由感應器髒污、位置偏移、線路鬆脫、反光干擾或 PLC I/O 訊號異常造成。",
        "checks": [
            "確認安全光柵、門蓋與急停狀態正常，並檢查感應器前方是否有油污、粉塵、殘料或治具遮擋。",
            "觀察感應器 LED 燈號與 HMI I/O 監看畫面，確認放入與移除工件時訊號是否同步切換。",
        ],
        "sop": [
            "停止自動循環，將機台切至手動或維修模式。",
            "清潔感應器鏡面與偵測區域，確認固定座無鬆動、線材接頭無脫落。",
            "依標準治具位置重新校正感應器角度與距離。",
            "於 HMI 清除 Err-302 警報，執行單步測試，確認 I/O 訊號穩定後恢復自動運轉。",
        ],
        "tpm": "建議把感應器清潔、固定螺絲確認與 I/O 燈號測試加入班前點檢，對高粉塵工站可縮短清潔週期並建立異常次數 Pareto 分析。",
    },
    "Err-105 實體卡料": {
        "category": "機構/機械問題",
        "summary": "物料、治具或半成品停留在非預期位置，常見原因包含輸送帶偏移、導軌間隙不當、料件變形、定位氣缸未到位或異物阻塞。",
        "checks": [
            "確認機台完全停止後再開啟護罩，禁止直接伸手進入夾治具、輸送帶或氣缸作動區。",
            "檢查卡料位置、導軌寬度、輸送帶張力與定位氣缸到位訊號，確認是否有變形料件或異物。",
        ],
        "sop": [
            "按下停止鍵，確認所有動作軸停止，必要時釋放殘壓後再處理。",
            "依物料流向反向或側向移除卡住料件，避免硬拉造成治具或感應器損壞。",
            "檢查導軌、擋塊、皮帶與氣缸是否偏移或鬆動，將料道恢復至標準位置。",
            "清除 Err-105 警報後，以慢速模式空跑一循環，再投入少量物料試產確認不卡料。",
        ],
        "tpm": "建議建立卡料位置紀錄表，將高頻卡料點納入改善專案，並於 PM 中加入導軌間隙、皮帶張力與治具磨耗量測。",
    },
}


MACHINE_NOTES = {
    "CNC-01": "高精度切削設備，需特別注意主軸負載、冷卻液狀態與夾治具定位。",
    "封裝機-A": "連續式封裝設備，需特別注意進料節拍、封口溫度、輸送帶與感測器潔淨度。",
    "點膠機-B": "精密塗佈設備，需特別注意膠壓、針頭堵塞、定位精度與環境溫濕度。",
}


st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #111827 48%, #1f2937 100%);
        color: #e5e7eb;
    }
    [data-testid="stSidebar"] {
        background: #111827;
        border-right: 1px solid #374151;
    }
    .main-title {
        padding: 22px 26px;
        border: 1px solid #4b5563;
        border-radius: 8px;
        background: linear-gradient(90deg, rgba(31, 41, 55, 0.95), rgba(17, 24, 39, 0.85));
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.28);
        margin-bottom: 18px;
    }
    .main-title h1 {
        margin: 0;
        color: #f9fafb;
        font-size: 34px;
        letter-spacing: 0;
    }
    .main-title p {
        margin: 8px 0 0 0;
        color: #cbd5e1;
        font-size: 16px;
    }
    .section-card {
        padding: 18px 20px;
        border: 1px solid #4b5563;
        border-radius: 8px;
        background: rgba(17, 24, 39, 0.82);
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
        margin-bottom: 16px;
    }
    .section-card h3 {
        margin: 0 0 10px 0;
        color: #f9fafb;
        font-size: 20px;
    }
    .status-pill {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 6px;
        background: #0f766e;
        color: #ecfeff;
        font-weight: 700;
        border: 1px solid #14b8a6;
        margin-right: 8px;
    }
    .warning-pill {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 6px;
        background: #7c2d12;
        color: #ffedd5;
        font-weight: 700;
        border: 1px solid #fb923c;
    }
    .report-box {
        padding: 22px 24px;
        border: 1px solid #64748b;
        border-radius: 8px;
        background: rgba(15, 23, 42, 0.9);
        margin-top: 12px;
    }
    .report-box h1, .report-box h2, .report-box h3 {
        color: #f8fafc;
    }
    .report-box li, .report-box p {
        color: #dbeafe;
        line-height: 1.75;
    }
    div[data-testid="stMetric"] {
        border: 1px solid #475569;
        border-radius: 8px;
        padding: 16px;
        background: rgba(30, 41, 59, 0.95);
    }
    div[data-testid="stMetricLabel"] {
        color: #cbd5e1;
    }
    div[data-testid="stMetricValue"] {
        color: #f8fafc;
    }
    .stButton > button {
        width: 100%;
        border: 1px solid #38bdf8;
        background: #0369a1;
        color: white;
        font-weight: 700;
        border-radius: 6px;
        padding: 0.7rem 1rem;
    }
    .stButton > button:hover {
        border-color: #7dd3fc;
        background: #075985;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


if "dashboard_updated" not in st.session_state:
    st.session_state.dashboard_updated = True


st.markdown(
    """
    <div class="main-title">
        <h1>🏭 智慧產線稼動率與異常排查看板</h1>
        <p>IE Production War Room Dashboard｜整合時間稼動率、停機比例與 AI Skill 異常診斷 SOP</p>
    </div>
    """,
    unsafe_allow_html=True,
)


with st.sidebar:
    st.markdown("## ⚙️ 參數選取與數據控制區")
    st.markdown("---")

    selected_machine = st.selectbox(
        "故障機台型號",
        options=list(MACHINE_NOTES.keys()),
        index=0,
    )

    selected_alarm = st.selectbox(
        "錯誤代碼 / Alarm Code",
        options=list(ALARM_KNOWLEDGE_BASE.keys()),
        index=0,
    )

    planned_time = st.slider(
        "計劃運轉時間（min）",
        min_value=120,
        max_value=480,
        value=480,
        step=10,
    )

    downtime = st.slider(
        "故障停機時間（min）",
        min_value=0,
        max_value=120,
        value=30,
        step=5,
    )

    update_button = st.button("更新戰情室看板", type="primary")

    if update_button:
        st.session_state.dashboard_updated = True

    st.markdown("---")
    st.info(MACHINE_NOTES[selected_machine])


left_column, right_column = st.columns([0.34, 0.66], gap="large")

actual_runtime = max(planned_time - downtime, 0)
availability_rate = (actual_runtime / planned_time) * 100 if planned_time > 0 else 0
alarm_info = ALARM_KNOWLEDGE_BASE[selected_alarm]


with left_column:
    st.markdown(
        f"""
        <div class="section-card">
            <h3>📌 目前通報資訊</h3>
            <p><span class="status-pill">機台</span>{selected_machine}</p>
            <p><span class="warning-pill">Alarm</span>{selected_alarm}</p>
            <p><b>初步分類：</b>{alarm_info["category"]}</p>
            <p><b>設備特性：</b>{MACHINE_NOTES[selected_machine]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="section-card">
            <h3>🧭 IE 判讀摘要</h3>
            <p>{alarm_info["summary"]}</p>
            <p><b>看板狀態：</b>已依目前參數完成稼動率估算與異常處置建議。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


with right_column:
    st.markdown(
        """
        <div class="section-card">
            <h3>📊 數據指標與圓餅圖表區</h3>
            <p>依據左側輸入之計劃運轉時間與故障停機時間，自動換算時間稼動率。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_col_1, metric_col_2, metric_col_3 = st.columns(3)
    metric_col_1.metric("計劃時間 (min)", f"{planned_time}")
    metric_col_2.metric("停機時間 (min)", f"{downtime}")
    metric_col_3.metric("時間稼動率 (%)", f"{availability_rate:.1f}")

    pie_fig = go.Figure(
        data=[
            go.Pie(
                labels=["實際運轉時間", "故障停機時間"],
                values=[actual_runtime, downtime],
                hole=0.42,
                marker=dict(colors=["#14b8a6", "#f97316"]),
                textinfo="label+percent",
                textfont=dict(size=16, color="#f8fafc"),
                hovertemplate="%{label}<br>%{value} min<br>%{percent}<extra></extra>",
            )
        ]
    )
    pie_fig.update_layout(
        title=dict(
            text="時間分配圓餅圖",
            font=dict(size=22, color="#f8fafc"),
            x=0.02,
        ),
        paper_bgcolor="rgba(15, 23, 42, 0.0)",
        plot_bgcolor="rgba(15, 23, 42, 0.0)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5,
            font=dict(color="#e5e7eb", size=14),
        ),
        margin=dict(l=20, r=20, t=70, b=40),
        height=430,
    )
    st.plotly_chart(pie_fig, use_container_width=True)


st.markdown("## 🤖 AI Skill 智慧診斷與總結區")

with st.expander("展開 / 收合：機台異常排查與處置報告", expanded=True):
    with st.container(border=True):
        st.markdown(
            f"""
# 🚨 【機台異常排查與處置報告】

## 一、 異常現況與初步分類
* **通報機台/代碼**：{selected_machine} / {selected_alarm}
* **故障可能類別**：{alarm_info["category"]}
* **異常摘要**：{alarm_info["summary"]}

## 二、 現場引導檢查確認（請依序確認）
1. 🛠️ **步驟一**：{alarm_info["checks"][0]}
2. 🛠️ **步驟二**：{alarm_info["checks"][1]}

## 三、 排除復歸步驟 (SOP)
* **復歸程序**：
  1. {alarm_info["sop"][0]}
  2. {alarm_info["sop"][1]}
  3. {alarm_info["sop"][2]}
  4. {alarm_info["sop"][3]}

* **💡 預防性維護建議**：{alarm_info["tpm"]}
        """
        )


st.caption("作業二作品｜智慧產線稼動率與異常排查看板｜Streamlit + Plotly")
