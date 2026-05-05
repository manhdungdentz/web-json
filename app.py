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
            # Thay đổi dấu gạch ngang thành dấu hai chấm để pd.to_datetime hiểu là giờ
            full_time = pd.to_datetime(f"{base_date} {t_str.replace('-', ':')}")
            data.append({"Thời gian": full_time, "Giá trị": float(val), "Khu": row['Tên khu']})
        except:
            continue
    return data

st.title("🌿 Ứng dụng Phân tích Dữ liệu Tưới Nhỏ Giọt")

# 3. NÚT TẢI FILE
uploaded_file = st.file_uploader("Chọn file dữ liệu", type=['json', 'csv'])

if uploaded_file:
    # Đọc dữ liệu
    if uploaded_file.name.endswith('.json'):
        df = pd.read_json(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file)
    
    # --- CHIẾN THUẬT MỚI: ÉP KIỂU THỦ CÔNG TỪNG DÒNG ---
    def super_safe_convert(x):
        try:
            # Chỉ lấy phần tử đầu tiên nếu nó là một list/danh sách
            if isinstance(x, list):
                x = x[0]
            # Chuyển về chuỗi, cắt khoảng trắng
            s = str(x).strip()
            # Thử chuyển đổi
            return pd.to_datetime(s, dayfirst=True, errors='coerce')
        except:
            return pd.NaT

    # Áp dụng hàm thủ công thay vì dùng pd.to_datetime trực tiếp lên cột
    df['Thời gian_DT'] = df['Thời gian'].apply(super_safe_convert)
    
    # Loại bỏ các dòng không thể xử lý
    df = df.dropna(subset=['Thời gian_DT'])
    
    # --- BỘ LỌC SIDEBAR ---
    st.sidebar.header("⚙️ Bộ lọc")
    
    if not df.empty:
        min_date = df['Thời gian_DT'].dt.date.min()
        max_date = df['Thời gian_DT'].dt.date.max()
        
        start_date = st.sidebar.date_input("Từ ngày", min_date)
        end_date = st.sidebar.date_input("Đến ngày", max_date)
        seed_val = st.sidebar.number_input("Table Seed", value=42)

        if st.sidebar.button("BẤM ĐỂ LỌC"):
            # Lọc dữ liệu
            mask = (df['Thời gian_DT'].dt.date >= start_date) & (df['Thời gian_DT'].dt.date <= end_date)
            df_filtered = df.loc[mask].copy()

            if not df_filtered.empty:
                tab1, tab2 = st.tabs(["📈 Biểu đồ chi tiết", "📋 Bảng dữ liệu"])

                with tab2:
                    st.subheader("Dữ liệu sau khi lọc")
                    st.dataframe(df_filtered.sample(frac=1, random_state=seed_val), use_container_width=True)

                with tab1:
                    # Tìm cột có chứa dữ liệu nén
                    complex_cols = [c for c in df.columns if df[c].astype(str).str.contains('/').any()]
                    
                    if complex_cols:
                        target_col = st.selectbox("Chọn chỉ số:", complex_cols)
                        chart_list = []
                        for _, row in df_filtered.iterrows():
                            # Lấy phần ngày YYYY-MM-DD
                            base_day = str(row['Thời gian_DT']).split(' ')[0]
                            chart_list.extend(parse_complex_data(row, target_col, base_day))
                        
                        if chart_list:
                            df_plot = pd.DataFrame(chart_list).sort_values('Thời gian')
                            fig = px.line(df_plot, x='Thời gian', y='Giá trị', color='Khu', markers=True)
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("Không trích xuất được dữ liệu chi tiết.")
                    else:
                        st.info("Không tìm thấy cột dữ liệu dạng nén (ví dụ: EC, PH).")
            else:
                st.error("Không có dữ liệu trong khoảng thời gian đã chọn.")
    else:
        st.error("Dữ liệu file không hợp lệ hoặc cột 'Thời gian' bị lỗi hoàn toàn.")
