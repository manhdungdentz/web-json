import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. Cấu hình trang
st.set_page_config(page_title="Hệ thống Dữ liệu Tưới", layout="wide")

# 2. Hàm xử lý dữ liệu nén
def parse_complex_data(row, col_name, base_date):
    content = str(row[col_name])
    if not content or content in ["0", "nan", "None"]:
        return []
    items = re.findall(r"(\d{2}-\d{2}-\d{2})/([\d.]+)", content)
    data = []
    for t_str, val in items:
        try:
            time_part = t_str.replace('-', ':')
            full_time = pd.to_datetime(f"{base_date} {time_part}")
            data.append({"Thời gian": full_time, "Giá trị": float(val), "Khu": row['Tên khu']})
        except:
            continue
    return data

st.title("🌿 Ứng dụng Phân tích Dữ liệu Tưới")

uploaded_file = st.file_uploader("Chọn file dữ liệu", type=['json', 'csv'])

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.json'):
            df = pd.read_json(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Lỗi đọc file: {e}")
        st.stop()

    # --- CHIẾN THUẬT: ÉP KIỂU TỪNG DÒNG (KHÔNG DÙNG .DT) ---
    def get_clean_datetime(val):
        try:
            v = val[0] if isinstance(val, list) else val
            dt = pd.to_datetime(str(v).strip(), dayfirst=True, errors='coerce')
            return dt
        except:
            return pd.NaT

    df['Thời gian_DT'] = df['Thời gian'].apply(get_clean_datetime)
    df = df.dropna(subset=['Thời gian_DT'])

    if not df.empty:
        # LẤY NGÀY THỦ CÔNG (Tránh dùng .dt.date vì hay lỗi)
        df['Ngay_Loc'] = df['Thời gian_DT'].apply(lambda x: x.date())
        
        st.sidebar.header("⚙️ Bộ lọc")
        min_d = min(df['Ngay_Loc'])
        max_d = max(df['Ngay_Loc'])
        
        start_date = st.sidebar.date_input("Từ ngày", min_d)
        end_date = st.sidebar.date_input("Đến ngày", max_d)
        seed_val = st.sidebar.number_input("Table Seed", value=42)

        if st.sidebar.button("BẤM ĐỂ LỌC"):
            # Lọc bằng giá trị đã tách
            mask = (df['Ngay_Loc'] >= start_date) & (df['Ngay_Loc'] <= end_date)
            df_filtered = df.loc[mask].copy()

            if not df_filtered.empty:
                tab1, tab2 = st.tabs(["📈 Biểu đồ chi tiết", "📋 Bảng dữ liệu"])

                with tab2:
                    st.dataframe(df_filtered.sample(frac=1, random_state=seed_val), use_container_width=True)

                with tab1:
                    complex_cols = [c for c in df.columns if df[c].astype(str).str.contains('/').any()]
                    
                    if complex_cols:
                        target_col = st.selectbox("Chọn chỉ số:", complex_cols)
                        chart_list = []
                        for _, row in df_filtered.iterrows():
                            # Ép kiểu string cho ngày
                            day_str = row['Thời gian_DT'].strftime('%Y-%m-%d')
                            chart_list.extend(parse_complex_data(row, target_col, day_str))
                        
                        if chart_list:
                            df_plot = pd.DataFrame(chart_list).sort_values('Thời gian')
                            fig = px.line(df_plot, x='Thời gian', y='Giá trị', color='Khu', markers=True)
                            st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Dữ liệu không có dạng nén (EC/PH).")
            else:
                st.warning("Không có dữ liệu trong khoảng này.")
    else:
        st.error("Không tìm thấy dữ liệu thời gian hợp lệ.")
