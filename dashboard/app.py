"""
Dashboard Streamlit untuk Mule Account Network Mapper.

Cara menjalankan: streamlit run dashboard/app.py

Dashboard ini menampilkan:
1. Ringkasan statistik
2. Daftar akun mencurigakan
3. Visualisasi network interaktif
4. Filter dan analisis mendalam
"""

import streamlit as st
import pandas as pd
import networkx as nx
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

#Tambah path agar bisa import dari src/
sys.path.append(os.path.join(os.path.dirname(__file__),'..'))

#Konfigurasi Halaman
st.set_page_config(
    page_title="Mule Account Network Mapper",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded"
)

#CSS custom untuk styling
st.markdown("""
<style>
    .metric-card {
        background-color: #1e1e2e;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid;
    }
    .high-risk { border-color: #ff4444; }
    .medium-risk { border-color: #ff8800; }
    .low-risk { border-color: #44bb44; }
    .stMetric { background-color: #16213e; border-radius: 8px; padding: 10px; }
</style>
""", unsafe_allow_html=True)

#Load Data
@st.cache_data
def load_data():
    """Cache data agar tidak reload setiap kali ada interaksi"""
    try:
        transactions = pd.read_csv('data/processed/transactions_clean.csv', dtype={'sender_account': str, 'receiver_account': str})
        fraud_results = pd.read_csv('data/output/fraud_detection_results.csv', dtype={'account_id': str})
        suspicious = pd.read_csv('data/output/suspicious_accounts.csv', dtype={'account_id': str})

        #Convert timestamp
        transactions['timestamp'] = pd.to_datetime(transactions['timestamp'])

        return transactions, fraud_results, suspicious
    except FileNotFoundError:
        st.error("❌ Data tidak ditemukan! Jalankan script data generation dan analysis terlebih dahulu.")
        st.code("python src/data_generator.py\npython src/data_cleaner.py\npython src/graph_analyzer.py\npython src/fraud_detector.py")
        st.stop()

#Sidebar
with st.sidebar:
    #st.image("https://via.placeholder.com/200x60/1e1e2e/ffffff?text=AML+System", width=200)
    st.title("⚙️ Filter & Pengaturan")

    risk_filter = st.multiselect(
        "Filter Risk Level:",
        options=['Sangat Tinggi', 'Tinggi', 'Sedang', 'Rendah'],
        default=['Sangat Tinggi', 'Tinggi']
    )

    min_amount = st.number_input("Min Total Transaksi (Rp):", value=0, step=100000)

    st.divider()
    st.markdown("**📖 Panduan Warna:**")
    st.markdown("🔴 Sangat Tinggi (Score > 70)")
    st.markdown("🟠 Tinggi (Score 51-70)")
    st.markdown("🟡 Sedang (Score 21-50)")
    st.markdown("🟢 Rendah (Score ≤ 20)")

#Load Data
transactions, fraud_results, suspicious = load_data()

#Header
st.title("🕵️ Mule Account Network Mapper")
st.markdown("**Anti-Money Laundering Intelligence Dashboard**")
st.divider()

#Baris 1: Metrik Utama
col1, col2, col3, col4, col5 = st.columns(5)

total_accounts = len(fraud_results)
very_high = len(fraud_results[fraud_results['risk_level'] == 'Sangat Tinggi'])
high = len(fraud_results[fraud_results['risk_level'] == 'Tinggi'])
total_transactions = len(transactions)
total_amount = transactions['amount'].sum()

with col1:
    st.metric("Total Rekening", f"{total_accounts:,}")

with col2:
    st.metric("🔴 Risiko Sangat Tinggi", very_high, delta=f"{very_high/total_accounts*100:.1f}% dari total")

with col3:
    st.metric("🟠 Risiko Tinggi", high, delta=f"{high/total_accounts*100:.1f}% dari total")

with col4:
    st.metric("Total Transaksi", f"{total_transactions:,}")

with col5:
    st.metric("Total Volume", f"Rp {total_amount/1e9:.2f}M")

st.divider()

#Baris 2: Charts
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📊 Distribusi Risk Level")

    risk_dist = fraud_results['risk_level'].value_counts().reset_index()
    risk_dist.columns = ['Risk Level', 'Jumlah Akun']

    color_map = {
        'Sangat Tinggi': '#ff4444',
        'Tinggi': '#ff8800',
        'Sedang': '#ffcc00',
        'Rendah': '#44bb44'
    }

    fig_pie = px.pie(
        risk_dist,
        values='Jumlah Akun',
        names='Risk Level',
        color='Risk Level',
        color_discrete_map=color_map,
        hole=0.4
    )
    fig_pie.update_layout(
        paper_bgcolor='rgba(0, 0, 0, 0)',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        font_color='white'
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col_right:
    st.subheader("📈 Distribusi Volume Transaksi per Jam")

    hourly = transactions.groupby('hour')['amount'].sum().reset_index()

    hourly.columns = ['Jam', 'Total Volume']

    #Tandai jam mencurigakan
    hourly['is_odd'] = hourly['Jam'].apply(lambda x: x >= 23 or x <= 4)

    fig_bar = px.bar(
        hourly,
        x='Jam',
        y='Total Volume',
        color='is_odd',
        color_discrete_map={True: '#ff4444', False: '#4488ff'},
        labels={'is_odd': 'Jam Mencurigakan'},
        title='Merah = Jam tidak wajar (23:00 - 04:00)'
    )
    fig_bar.update_layout(
        paper_bgcolor='rgba(0, 0, 0, 0)',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        font_color='white',
        showlegend=False
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

#Baris 3: Tabel Akun Mencurigakan
st.subheader("🚨 Daftar Akun Mencurigakan")

#Filter berdasarkan sidebar
filtered_df = fraud_results[
    (fraud_results['risk_level'].isin(risk_filter)) &
    (fraud_results['total_received'] >= min_amount)
].copy()

#Format tampilan
display_df = filtered_df[[
    'account_id', 'risk_level', 'risk_score',
    'in_degree', 'out_degree', 'total_received',
    'total_sent', 'pagerank_score', 'triggered_rules'
]].copy()

display_df['total_received'] = display_df['total_received'].apply(lambda x: f"Rp{x:,.0f}")
display_df['total_sent'] = display_df['total_sent'].apply(lambda x: f"Rp {x:,.0f}")
display_df['pagerank_score'] = display_df['pagerank_score'].apply(lambda x: f"{x:.1f}")
display_df['risk_score'] = display_df['risk_score'].apply(lambda x: f"{x:.0f}/100")

display_df.columns = [
    'Account ID', 'Risk Level', 'Risk Score',
    'In-Degree', 'Out-Degree', 'Total Diterima',
    'Total Dikirim', 'PageRank', 'Rule Terpicu'
]

#Color-code tabel berdasarkan risk level
def color_risk(val):
    colors = {
        'Sangat Tinggi': 'background-color: rgba(255,68,68,0.3)',
        'Tinggi': 'background-color: rgba(255,136,0,0.3)',
        'Sedang': 'background-color: rgba(255,204,0,0.3)',
        'Rendah': 'background-color: rgba(68,187,68,0.3)',
    }
    return colors.get(val, '')

st.write(f"Menampilkan **{len(display_df)}** akun")
st.dataframe(
    display_df.style.applymap(color_risk, subset=['Risk Level']),
    use_container_width=True,
    height=400
)

#Download button
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="⬇️ Download Hasil (CSV)",
    data=csv,
    file_name="suspicious_accounts.csv",
    mime="text/csv"
)

st.divider()

#Baris 4: Detail Akun
st.subheader("🔎 Analisis Detail Akun")

selected_account = st.selectbox(
    "Pilih akun untuk dilihat detailnya: ",
    options=filtered_df['account_id'].tolist()
)

if selected_account:
    account_data = fraud_results[fraud_results['account_id'] == selected_account].iloc[0]

    col_d1, col_d2, col_d3 = st.columns(3)

    with col_d1:
        st.markdown("**📋 Profil Akun: ")
        st.write(f"**Account ID:** {account_data['account_id']}")
        st.write(f"**Risk Level:** {account_data['risk_level']}")
        st.write(f"**Risk Score:** {account_data['risk_score']:.0f}/100")
        st.write(f"**PageRank Score:** {account_data['pagerank_score']:.2f}")
    
    with col_d2:
        st.markdown("**💰 Aktivitas Keuangan: ")
        st.write(f"**Total Diterima:** Rp {account_data['total_received']:,.0f}")
        st.write(f"**Total Dikirim:** Rp {account_data['total_sent']:,.0f}")
        st.write(f"**Net Flow:** Rp {account_data['net_flow']:,.0f}")
    
    with col_d3:
        st.markdown("**🔗 Koneksi Jaringan:**")
        st.write(f"**In-Degree (penerima dari):** {account_data['in_degree']:.0f}")
        st.write(f"**Out-Degree (pengirim ke):** {account_data['out_degree']:.0f}")
        st.write(f"**Total Koneksi:** {account_data['total_degree']:.0f}")
    
    #Rule yang terpicu
    if pd.notna(account_data['triggered_rules']) and account_data['triggered_rules']:
        st.markdown("**⚠️ Rule yang Terpicu:**")
        for rule in str(account_data['triggered_rules']).split(';'):
            rule = rule.strip()
            if rule:
                st.error(f"🚨 {rule}")
    
    #Riwayat transaksi akun ini
    st.markdown("**📑 Riwayat Transaksi:**")
    account_txns = transactions[
        (transactions['sender_account'] == selected_account) |
        (transactions['receiver_account'] == selected_account)
    ].sort_values('timestamp', ascending=False).head(20)

    if len(account_txns) > 0:
        account_txns['direction'] = account_txns.apply(
            lambda r: '⬆️ Kirim' if r['sender_account'] == selected_account else '⬇️ Terima',
            axis=1
        )
        account_txns['counterpart'] = account_txns.apply(
            lambda r: r['receiver_account'] if r['sender_account'] == selected_account else r['sender_account'],
            axis=1
        )
        st.dataframe(
            account_txns[['timestamp', 'direction', 'counterpart', 'amount', 'transaction_type']].rename(
                columns={'timestamp': 'Waktu', 'direction': 'Arah', 'counterpart': 'Rekening Lawan', 'amount': 'Jumlah', 'transaction_type': 'Jenis'}
            ),
            use_container_width=True
        )
st.divider()
st.markdown("*Dashboard ini dibuat untuk keperluan porfolio AML Analytics. Data bersifat simulasi.")