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
    
    # --- BƯỚC 1: ÉP KIỂU VÀ DỌN RÁC TRIỆT ĐỂ ---
    # Ép về datetime, dòng nào lỗi sẽ thành NaT
    df['Thời gian_DT'] = pd.to_datetime(df['Thời gian'], dayfirst=True, errors='coerce')
    
    # Xóa sạch các dòng NaT trước khi làm bất cứ việc gì tiếp theo
    df = df.dropna(subset=['Thời gian_DT'])

    if not df.empty:
        st.sidebar.header("⚙️ Bộ lọc")
        
        # --- BƯỚC 2: CHUYỂN CỘT SANG DẠNG DATE ĐỂ SO SÁNH ---
        # Tạo một cột phụ chỉ chứa Ngày (không có Giờ) để tránh lỗi so sánh
        df['Ngày_Chỉ_Định'] = df['Thời gian_DT'].dt.date
        
        min_date = df['Ngày_Chỉ_Định'].min()
        max_date = df['Ngày_Chỉ_Định'].max()
        
        start_date = st.sidebar.date_input("Từ ngày", min_date)
        end_date = st.sidebar.date_input("Đến ngày", max_date)
        seed_val = st.sidebar.number_input("Table Seed", value=42)

        if st.sidebar.button("BẤM ĐỂ LỌC"):
            # --- BƯỚC 3: LỌC AN TOÀN ---
            mask = (df['Ngày_Chỉ_Định'] >= start_date) & (df['Ngày_Chỉ_Định'] <= end_date)
            df_filtered = df.loc[mask].copy()

            if not df_filtered.empty:
                tab1, tab2 = st.tabs(["📈 Biểu đồ chi tiết", "📋 Bảng dữ liệu"])

                with tab2:
                    st.subheader("Dữ liệu sau khi lọc")
                    st.dataframe(df_filtered.sample(frac=1, random_state=seed_val), use_container_width=True)

                with tab1:
                    complex_cols = [c for c in df.columns if df[c].astype(str).str.contains('/').any()]
                    
                    if complex_cols:
                        target_col = st.selectbox("Chọn chỉ số:", complex_cols)
                        chart_list = []
                        for _, row in df_filtered.iterrows():
                            # Dùng format ngày chuẩn để bung dữ liệu nén
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
    else:
        st.error("File dữ liệu không có thông tin ngày tháng hợp lệ.")
