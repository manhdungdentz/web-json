if uploaded_file:
        # Đọc file
        if uploaded_file.name.endswith('.json'):
            df = pd.read_json(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)
        
        # 1. Ép tất cả về chuỗi và xử lý thời gian (Thẳng hàng với dòng 32)
        df['Thời gian'] = df['Thời gian'].astype(str).str.strip()
        
        def force_convert_date(x):
            try:
                return pd.to_datetime(x, errors='coerce', dayfirst=True)
            except:
                return pd.NaT

        df['Thời gian_DT'] = df['Thời gian'].apply(force_convert_date)
        df = df.dropna(subset=['Thời gian_DT'])
        df['Thời gian_DT'] = pd.to_datetime(df['Thời gian_DT'])
        
        # --- BỘ LỌC SIDEBAR ---
        st.sidebar.header("⚙️ Bộ lọc")
        
        min_date = df['Thời gian_DT'].min().date()
        max_date = df['Thời gian_DT'].max().date()
        start_date = st.sidebar.date_input("Từ ngày", min_date)
        end_date = st.sidebar.date_input("Đến ngày", max_date)
        seed_val = st.sidebar.number_input("Table Seed", value=42)
        
        if st.sidebar.button("BẤM ĐỂ LỌC"):
            # Lọc dữ liệu an toàn (Dòng 67 tối ưu)
            mask = (df['Thời gian_DT'].dt.date >= start_date) & (df['Thời gian_DT'].dt.date <= end_date)
            df_filtered = df.loc[mask].copy()
  
