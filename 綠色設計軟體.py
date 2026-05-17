Python 3.13.2 (tags/v3.13.2:4f8bb39, Feb  4 2025, 15:23:48) [MSC v.1942 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license()" for more information.
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- 1. 系統網頁基本設定 ---
st.set_page_config(
    page_title="EcoDesign Optima 產品綠色循環設計決策系統",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🍀 EcoDesign Optima：產品綠色循環設計與永續決策輔助系統")
st.caption("本系統整合層級分析法 (AHP)、品質機能展開 (QFD) 與三維度永續指標（拆解時間、成本、碳足跡）之優化決策工具")
st.markdown("---")

# --- 2. 側邊欄：AHP 決策權重與精確一致性檢定 ---
st.sidebar.header("🛠️ 步驟一：AHP 綠色指標權重設定")
st.sidebar.write("請評估大方向指標的相對重要程度 (1-9)：")

# 定義準則名稱
criteria = ["可拆解性 (C1)", "環境衝擊 (C2)", "功能結構 (C3)"]
n = len(criteria)

# 讓使用者在側邊欄輸入成對比較矩陣（建立上三角即可）
c1_vs_c2 = st.sidebar.slider("可拆解性 (C1) 相對 環境衝擊 (C2)", 1/9, 9.0, 3.0, step=0.5 if c1_vs_c2 >=1 else 0.05)
c1_vs_c3 = st.sidebar.slider("可拆解性 (C1) 相對 功能結構 (C3)", 1/9, 9.0, 2.0, step=0.5)
c2_vs_c3 = st.sidebar.slider("環境衝擊 (C2) 相對 功能結構 (C3)", 1/9, 9.0, 0.5, step=0.1)

# 構建 AHP 成對比較矩陣
ahp_matrix = np.zeros((n, n))
# 對角線為 1
np.fill_diagonal(ahp_matrix, 1.0)
# 填入使用者設定值
ahp_matrix[0, 1] = c1_vs_c2
ahp_matrix[0, 2] = c1_vs_c3
ahp_matrix[1, 2] = c2_vs_c3
# 填入倒數值
ahp_matrix[1, 0] = 1.0 / c1_vs_c2
ahp_matrix[2, 0] = 1.0 / c1_vs_c3
ahp_matrix[2, 1] = 1.0 / c2_vs_c3

# --- AHP 數學矩陣運算 ---
# 1. 幾何平均法求特徵向量 (權重)
geom_mean = np.prod(ahp_matrix, axis=1) ** (1/n)
ahp_weights = geom_mean / np.sum(geom_mean)

# 2. 一致性檢定計算 (AW = lambda * W)
AW = np.dot(ahp_matrix, ahp_weights)
lambda_max = np.mean(AW / ahp_weights)
CI = (lambda_max - n) / (n - 1) if n > 1 else 0
RI_dict = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12} # 隨機指標對照表
RI = RI_dict[n]
CR = CI / RI if RI > 0 else 0

# 側邊欄顯示檢定結果
if CR < 0.1:
    st.sidebar.success(f"✅ 一致性檢定通過！\nC.R. = {CR:.4f} (< 0.1)")
else:
    st.sidebar.error(f"❌ 一致性檢定未通過！\nC.R. = {CR:.4f} (>= 0.1)，請重新調整滑桿。")

st.sidebar.write("**🎯 準則權重計算結果：**")
weight_df = pd.DataFrame({"指標": criteria, "權重": ahp_weights})
st.sidebar.dataframe(weight_df.style.format({"權重": "{:.3f}"}), hide_index=True)


# --- 3. 主畫面功能分頁 (Tabs) ---
tab1, tab2, tab3 = st.tabs(["📋 BOM 與工程屬性設定", "🧮 QFD 品質屋轉譯", "📊 3D 永續決策看板"])

# 預設手電筒案例數據
if 'bom_data' not in st.session_state:
    st.session_state.bom_data = pd.DataFrame({
        "零件名稱": ["手電筒筒身", "電池模組", "LED燈頭", "開關橡膠帽"],
        "重量(kg)": [0.15, 0.08, 0.03, 0.01],
        "碳排係數(kgCO2e/kg)": [6.5, 25.0, 1500.0, 6.4],
        "循環恢復指數(CI)": [0.8, 0.2, 0.1, 0.5],
        "基準拆解時間(Ts)": [5.0, 10.0, 12.0, 4.0],
        "校正因子_連接(CF1)": [1.2, 1.5, 2.0, 1.1],
        "校正因子_工具(CF2)": [1.0, 1.2, 1.5, 1.0],
        "校正因子_接近(CF3)": [1.1, 1.3, 1.6, 1.0]
    })

# --- TAB 1: BOM 與工程屬性設定 ---
with tab1:
    st.header("⚙️ 產品物料清單 (BOM) 與拆解因子設定")
    st.write("您可以在下方表格中直接雙擊修改任何實體數據（如重量、CF值），系統將即時動態更新所有分析：")
    
    # 讓使用者動態編輯 BOM 表
    edited_bom = st.data_editor(st.session_state.bom_data, num_rows="dynamic", key="bom_editor")
    st.session_state.bom_data = edited_bom

    with st.expander("💡 填寫說明與專題公式對照"):
        st.markdown("""
        * **基準拆解時間 ($Ts$)**：在理想狀態下的基本拆卸時間。
        * **校正因子 ($CF_k$)**：考慮到接觸型態、工具需求、接近性等工程限制的放大倍率。
        * **拆解時間公式**： $T_i = T_s \\times \\prod(CF_k) = T_s \\times CF_1 \\times CF_2 \\times CF_3$
        * **碳足跡公式**： $CF_i = w_i \\times e_i \\times (1 - CI_i)$ 
          *(其中 $w$ 為重量，$e$ 為碳排係數，$CI$ 為循環恢復指數)*
        """)

# --- TAB 2: QFD 品質屋轉譯 ---
with tab2:
    st.header("🏠 品質屋 (QFD) 零件重要度轉譯")
    st.write("請評估各零件與 AHP 綠色指標之工程關聯分數（請填入：1-微弱相關、3-中等相關、9-高度相關）：")
    
    # 根據目前的 BOM 零件動態產生 QFD 評分矩陣
    parts_list = edited_bom["零件名稱"].tolist()
    
    # 初始化或維持 QFD 數據
    qfd_init = {"零件名稱": parts_list, "可拆解性關聯": [9, 9, 3, 1], "環境衝擊關聯": [3, 9, 9, 3], "功能結構關聯": [9, 3, 9, 9]}
    # 確保列數與目前BOM同步
    if len(parts_list) != 4:
        qfd_init = {"零件名稱": parts_list, "可拆解性關聯": [3]*len(parts_list), "環境衝擊關聯": [3]*len(parts_list), "功能結構關聯": [3]*len(parts_list)}
        
    edited_qfd = st.data_editor(pd.DataFrame(qfd_init), key="qfd_editor")
    
    # 計算 QFD 綜合得分 (矩陣相乘：QFD關聯分數 * AHP權重)
    qfd_scores = []
    for idx, row in edited_qfd.iterrows():
        score = (row["可拆解性關聯"] * ahp_weights[0] + 
                 row["環境衝擊關聯"] * ahp_weights[1] + 
                 row["功能結構關聯"] * ahp_weights[2])
        qfd_scores.append(score)
        
    edited_bom["QFD工程重要度"] = qfd_scores


# --- TAB 3: 3D 永續決策看板 ---
with tab3:
    st.header("📊 三維度永續效益與關鍵零件篩選")
    
    # --- 後台核心公式運算引擎 ---
    # 1. 計算實際拆解時間
    edited_bom["計算拆解時間(秒)"] = (
        edited_bom["基準拆解時間(Ts)"] * edited_bom["校正因子_連接(CF1)"] * edited_bom["校正因子_工具(CF2)"] * edited_bom["校正因子_接近(CF3)"]
...     )
...     
...     # 2. 計算碳足跡
...     edited_bom["計算碳足跡(kgCO2e)"] = (
...         edited_bom["重量(kg)"] * edited_bom["碳排係數(kgCO2e/kg)"] * (1 - edited_bom["循環恢復指數(CI)"])
...     )
...     
...     # 3. 計算拆解成本 (設定基準工資率：190.08 元/小時 -> 每秒約 0.0528 元)
...     wage_per_second = 190.08 / 3600
...     edited_bom["拆解成本(元)"] = edited_bom["計算拆解時間(秒)"] * wage_per_second
...     
...     # --- 中位數篩選法門檻計算 ---
...     median_qfd = edited_bom["QFD工程重要度"].median()
...     median_time = edited_bom["計算拆解時間(秒)"].median()
...     median_cf = edited_bom["計算碳足跡(kgCO2e)"].median()
...     
...     # 佈局：上方呈現 KPI 指標
...     kpi1, kpi2, kpi3 = st.columns(3)
...     kpi1.metric("產品總碳足跡 (kgCO2e)", f"{edited_bom['計算碳足跡(kgCO2e)'].sum():.3f}")
...     kpi2.metric("總拆解時間 (秒)", f"{edited_bom['計算拆解時間(秒)'].sum():.1f}")
...     kpi3.metric("總拆解人工成本 (元)", f"{edited_bom['拆解成本(元)'].sum():.2f}")
...     
...     st.markdown("---")
...     
...     # 佈局：左邊放 3D 圖，右邊放中位數優化決策
...     chart_col, decision_col = st.columns([3, 2])
...     
...     with chart_col:
...         st.subheader("🌐 互動式 3D 三軸綠色設計看板")
...         st.caption("X軸：拆解時間 | Y軸：拆解成本 | Z軸：碳足跡。球體大小代表該零件的碳足跡嚴重性。")
...         
...         # 繪製 3D 散佈圖
...         fig = px.scatter_3d(
            edited_bom,
            x="計算拆解時間(秒)",
            y="拆解成本(元)",
            z="計算碳足跡(kgCO2e)",
            color="零件名稱",
            size="計算碳足跡(kgCO2e)",
            text="零件名稱",
            hover_data=["重量(kg)", "QFD工程重要度"],
            height=600
        )
        
        fig.update_layout(
            scene=dict(
                xaxis_title='拆解時間 (秒)',
                yaxis_title='拆解成本 (元)',
                zaxis_title='碳足跡 (kgCO2e)'
            ),
            margin=dict(l=0, r=0, b=0, t=0)
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with decision_col:
        st.subheader("💡 專題決策：中位數關鍵零件篩選")
        st.write(f"系統自動計算當前產品的中位數門檻：\n* QFD重要度中位數：`{median_qfd:.2f}`\n* 拆解時間中位數：`{median_time:.1f} 秒`")
        
        # 篩選出大於中位數的瓶頸關鍵零件
        bottlenecks = edited_bom[
            (edited_bom["QFD工程重要度"] >= median_qfd) | 
            (edited_bom["計算拆解時間(秒)"] >= median_time) |
            (edited_bom["計算碳足跡(kgCO2e)"] >= median_cf)
        ]
        
        st.markdown("**🚨 系統偵測之關鍵改善瓶頸零件：**")
        if not bottlenecks.empty:
            for _, row in bottlenecks.iterrows():
                with st.container(border=True):
                    st.write(f"⚠️ **【{row['零件名稱']}】**")
                    # 判斷是哪一項超標
                    reasons = []
                    if row["QFD工程重要度"] >= median_qfd: reasons.append(f"QFD 權重高 ({row['QFD工程重要度']:.2f})")
                    if row["計算拆解時間(秒)"] >= median_time: reasons.append(f"拆解耗時 ({row['計算拆解時間(秒)']:.1f}秒)")
                    if row["計算碳足跡(kgCO2e)"] >= median_cf: reasons.append(f"環境碳負荷高 ({row['計算碳足跡(kgCO2e)']:.2f} kgCO2e)")
                    
                    st.write(f"  * **超標原因**：{', '.join(reasons)}")
                    
                    # 根據瓶頸給予優化設計的IE建議
                    if row["計算拆解時間(秒)"] >= median_time:
                        st.info("💡 **設計優化策略**：建議降低連接校正因子 ($CF_1$)，如將螺絲固定改為快拆卡扣，或優化定位空間以縮短拆解時間。")
                    if row["計算碳足跡(kgCO2e)"] >= median_cf:
                        st.success("🌱 **材料循環策略**：建議更換低環境衝擊材料（降低 $e_i$）或提高其結構可回收性（提升 $CI$ 指數）。")
        else:
            st.success("🎉 目前所有零件指標皆在良性範圍內！")

    # 顯示完整計算後的報表資料
    st.markdown("---")
    st.subheader("📊 完整永續量化評估報表")
    st.dataframe(
        edited_bom[[
            "零件名稱", "QFD工程重要度", "計算拆解時間(秒)", 
            "拆解成本(元)", "計算碳足跡(kgCO2e)"
        ]].style.format({
            "QFD工程重要度": "{:.2f}",
            "計算拆解時間(秒)": "{:.1f}",
            "拆解成本(元)": "{:.2f}",
            "計算碳足跡(kgCO2e)": "{:.4f}"
        }), 
        use_container_width=True,
        hide_index=True
