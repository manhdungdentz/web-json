import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. Cấu hình trang
st.set_page_config(page_title="Hệ thống Dữ liệu Tưới", layout="wide")

# 2. Hàm xử lý dữ liệu nén
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

uploaded_file = st.file_uploader("Chọn file dữ liệu", type=['json', 'csv'])

if uploaded_file:
    if uploaded_file.name.endswith('.json'):
        df = pd.read_json(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file)
    
    # --- XỬ LÝ THỜI GIAN SIÊU CẤP ---
    # Ép kiểu thủ công từng ô để tránh lỗi mixed_inputs
    def force_convert(x):
        try:
            return pd.to_datetime(str(x).strip(), dayfirst=True, errors='coerce')
        except:
            return pd.NaT

    df['Thời gian_DT'] = df['Thời gian'].apply(force_convert)
    df = df.dropna(subset=['Thời gian_DT'])
    
    # Ép kiểu lại một lần nữa bằng to_datetime để kích hoạt thuộc tính .dt
    df['Thời gian_DT'] = pd.to_datetime(df['Thời gian_DT'], errors='coerce')

    st.sidebar.header("⚙️ Bộ lọc")
    
    # SỬA LỖI DÒNG 60: Dùng pd.to_datetime bọc ngoài để chắc chắn có thuộc tính .dt
    try:
        # Chuyển đổi cột sang DatetimeIndex để lấy ngày cực kỳ an toàn
        all_dates = pd.DatetimeIndex(df['Thời gian_DT']).date
        min_date = all_dates.min()
        max_date = all_dates.max()
        
        start_date = st.sidebar.date_input("Từ ngày", min_date)
        end_date = st.sidebar.date_input("Đến ngày", max_date)
        seed_val = st.sidebar.number_input("Table Seed", value=42)

        if st.sidebar.button("BẤM ĐỂ LỌC"):
            # Lọc dữ liệu dùng DatetimeIndex để tránh lỗi .dt
            mask = (pd.DatetimeIndex(df['Thời gian_DT']).date >= start_date) & \
                   (pd.DatetimeIndex(df['Thời gian_DT']).date <= end_date)
            df_filtered = df.loc[mask].copy()

            if not df_filtered.empty:
                tab1, tab2 = st.tabs(["📈 Biểu đồ chi tiết", "📋 Bảng dữ liệu"])

                with tab2:
                    st.subheader("Dữ liệu sau khi lọc")
                    st.dataframe(df_filtered.sample(frac=1, random_state=seed_val), use_container_width=True)

                with tab1:
                    # Tìm cột EC/PH
                    complex_cols = [c for c in df.columns if df[c].astype(str).str.contains('/').any()]
                    
                    if complex_cols:
                        target_col = st.selectbox("Chọn chỉ số:", complex_cols)
                        chart_list = []
                        for _, row in df_filtered.iterrows():
                            # Lấy ngày theo định dạng YYYY-MM-DD
                            base_day = row['Thời gian_DT'].strftime('%Y-%m-%d')
                            chart_list.extend(parse_complex_data(row, target_col, base_day))
                        
                        if chart_list:
                            df_plot = pd.DataFrame(chart_list).sort_values('Thời gian')
                            fig = px.line(df_plot, x='Thời gian', y='Giá trị', color='Khu', markers=True)
                            st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Không tìm thấy dữ liệu EC/PH.")
            else:
                st.error("Không tìm thấy dữ liệu trong khoảng ngày này.")
    except Exception as e:
        st.error(f"Lỗi định dạng ngày tháng: {e}")
