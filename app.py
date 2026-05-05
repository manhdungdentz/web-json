import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. Cấu hình trang
st.set_page_config(page_title="Hệ thống Dữ liệu Tưới", layout="wide")

# 2. Hàm xử lý dữ liệu nén (EC, PH...)
def parse_complex_data(row, col_name, base_date):
    content = str(row[col_name])
    if not content or content == "0" or content == "nan":
        return []
    items = re.findall(r"(\d{2}-\d{2}-\d{2})/([\d.]+)", content)
    data = []
    for t_str, val in items:
        try:
            full_time = pd.to_datetime(f"{base_date} {t_str.replace('-', ':')}")
            data.append({"Thời gian": full_time, "Giá trị": float(val), "Khu": row['Tên khu']})
        except:
            continue
    return data

st.title("🌿 Ứng dụng Phân tích Dữ liệu Tưới Nhỏ Giọt")

# 3. NÚT TẢI FILE (Quan trọng nhất - Thiếu dòng này sẽ bị NameError)
uploaded_file = st.file_uploader("Chọn file dữ liệu", type=['json', 'csv'])

if uploaded_file:
 # Đọc dữ liệu
    if uploaded_file.name.endswith('.json'):
        df = pd.read_json(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file)
    
    # --- LỚP 1: ÉP KIỂU TỪNG DÒNG ---
    def final_convert(x):
        try:
            return pd.to_datetime(str(x).strip(), dayfirst=True, errors='coerce')
        except:
            return pd.NaT

    df['Thời gian_DT'] = df['Thời gian'].apply(final_convert)
    
    # --- LỚP 2: XÓA DÒNG LỖI VÀ ÉP KIỂU CỨNG ---
    df = df.dropna(subset=['Thời gian_DT'])
    df['Thời gian_DT'] = pd.to_datetime(df['Thời gian_DT']) # Ép lần cuối để kích hoạt .dt

    # --- BỘ LỌC SIDEBAR ---
    st.sidebar.header("⚙️ Bộ lọc")
    
    # Lấy ngày nhỏ nhất và lớn nhất an toàn
    min_date = df['Thời gian_DT'].dt.date.min()
    max_date = df['Thời gian_DT'].dt.date.max()
    
    start_date = st.sidebar.date_input("Từ ngày", min_date)
    end_date = st.sidebar.date_input("Đến ngày", max_date)
    seed_val = st.sidebar.number_input("Table Seed", value=42)

    if st.sidebar.button("BẤM ĐỂ LỌC"):
        # --- LỚP 3: LỌC DỮ LIỆU AN TOÀN ---
        # Chuyển đổi sang kiểu date trước khi so sánh để tránh lệch kiểu dữ liệu
        current_dates = df['Thời gian_DT'].dt.date
        mask = (current_dates >= start_date) & (current_dates <= end_date)
        df_filtered = df.loc[mask].copy()

        with tab1:
            complex_cols = [c for c in df.columns if "/" in str(df[c].iloc[-1])]
            if complex_cols:
                target_col = st.selectbox("Chọn chỉ số:", complex_cols)
                chart_list = []
                for _, row in df_filtered.iterrows():
                    base_day = str(row['Thời gian']).split(' ')[0]
                    chart_list.extend(parse_complex_data(row, target_col, base_day))
                
                if chart_list:
                    df_plot = pd.DataFrame(chart_list).sort_values('Thời gian')
                    fig = px.line(df_plot, x='Thời gian', y='Giá trị', color='Khu', markers=True)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Không tìm thấy dữ liệu nén để vẽ biểu đồ.")
