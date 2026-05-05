import streamlit as st
import pandas as pd
import plotly.express as px
import re

# Cấu hình trang web
st.set_page_config(page_title="Hệ thống Dữ liệu Tưới", layout="wide")

# Hàm xử lý chuỗi nén "14-01-01/32.35"
def parse_complex_data(row, col_name, base_date):
    content = str(row[col_name])
    if not content or content == "0" or content == "nan":
        return []
    # Tìm tất cả các cụm Giờ-Phút-Giây/GiáTrị
    items = re.findall(r"(\d{2}-\d{2}-\d{2})/([\d.]+)", content)
    data = []
    for t_str, val in items:
        # Chuyển thành định dạng thời gian chuẩn
        full_time = pd.to_datetime(f"{base_date} {t_str.replace('-', ':')}")
        data.append({"Thời gian": full_time, "Giá trị": float(val), "Khu": row['Tên khu']})
    return data

st.title("🌿 Ứng dụng Phân tích Dữ liệu Tưới Nhỏ Giọt")
st.markdown("Tải file JSON/CSV lên để xem biểu đồ và lọc dữ liệu.")

# 1. NHẬN DỮ LIỆU
uploaded_file = st.file_uploader("Chọn file dữ liệu", type=['json', 'csv'])

if uploaded_file:
    # Đọc file
    if uploaded_file.name.endswith('.json'):
        df = pd.read_json(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file)
    
 # 1. Ép tất cả về chuỗi và xóa khoảng trắng dư thừa
    df['Thời gian'] = df['Thời gian'].astype(str).str.strip()
    
    # 2. Định nghĩa hàm chuyển đổi cực mạnh (xử lý từng dòng)
    def force_convert_date(x):
        try:
            # Thử chuyển đổi tự động với định dạng hỗn hợp
            return pd.to_datetime(x, errors='coerce', dayfirst=True)
        except:
            return pd.NaT

    # 3. Áp dụng chuyển đổi và xóa bỏ dữ liệu lỗi
    df['Thời gian_DT'] = df['Thời gian'].apply(force_convert_date)
    df = df.dropna(subset=['Thời gian_DT'])
    
    # 4. Đảm bảo dữ liệu là kiểu ngày tháng thực thụ trước khi lọc
    df['Thời gian_DT'] = pd.to_datetime(df['Thời gian_DT'])
    
    # 4. Xóa dòng lỗi
    df = df.dropna(subset=['Thời gian_DT'])
    
    # --- BỘ LỌC SIDEBAR ---
    st.sidebar.header("⚙️ Bộ lọc")
    
    # Lọc thời gian
    min_date = df['Thời gian_DT'].min().date()
    max_date = df['Thời gian_DT'].max().date()
    start_date = st.sidebar.date_input("Từ ngày", min_date)
    end_date = st.sidebar.date_input("Đến ngày", max_date)
    
    # Table Seed
    seed_val = st.sidebar.number_input("Table Seed", value=42)
    
    # Nút bấm lọc
    if st.sidebar.button("BẤM ĐỂ LỌC"):
        # Lọc dữ liệu thô
        mask = (df['Thời gian_DT'].dt.date >= start_date) & (df['Thời gian_DT'].dt.date <= end_date)
        df_filtered = df.loc[mask]
        
        # Áp dụng Seed để xáo trộn bảng hiển thị
        df_display = df_filtered.sample(frac=1, random_state=seed_val)

        # HIỂN THỊ
        tab1, tab2 = st.tabs(["📈 Biểu đồ chi tiết", "📋 Bảng dữ liệu"])

        with tab2:
            st.subheader(f"Dữ liệu gốc (Seed: {seed_val})")
            st.dataframe(df_display, use_container_width=True)

        with tab1:
            # Tự động tìm các cột có chứa chuỗi nén (EC, PH...)
            complex_cols = [c for c in df.columns if "/" in str(df[c].iloc[-1])]
            
            if complex_cols:
                target_col = st.selectbox("Chọn chỉ số muốn xem biểu đồ:", complex_cols)
                
                # Bung dữ liệu nén
                chart_list = []
                for _, row in df_filtered.iterrows():
                    base_day = str(row['Thời gian']).split(' ')[0]
                    chart_list.extend(parse_complex_data(row, target_col, base_day))
                
                if chart_list:
                    df_plot = pd.DataFrame(chart_list).sort_values('Thời gian')
                    fig = px.line(df_plot, x='Thời gian', y='Giá trị', color='Khu', markers=True)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Không có dữ liệu chi tiết.")
            else:
                st.info("File này không chứa dữ liệu chuỗi thời gian nén.")
