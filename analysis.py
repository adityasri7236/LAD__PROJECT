import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("🔐 Login Anomaly Detection System")

# ✅ FILE UPLOADER
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:

    # Load uploaded file
    st_autorefresh(interval=5000, key="refresh")  # every 5 sec
    df = pd.read_csv(uploaded_file)

    st.subheader("📄 Uploaded Data")
    st.write(df.head())

    # Data Cleaning
    df['login_time'] = pd.to_datetime(df['login_time'], errors='coerce')
    df.dropna(inplace=True)
    df['hour'] = df['login_time'].dt.hour

    st.subheader("🧹 Cleaned Data")
    st.write(df.head())

    # Failed logins
    failed = df[df['status'] == 'failed']
    st.write("❌ Total Failed Logins:", len(failed))

    # Failed per IP
    ip_fail = failed.groupby('ip_address').size().reset_index(name='fail_count')
    st.subheader("🌐 Failed Logins per IP")
    st.write(ip_fail)

    # Suspicious IPs
    suspicious_ips = ip_fail[ip_fail['fail_count'] > 3]
    st.subheader("🚨 Suspicious IPs")
    st.write(suspicious_ips)

    # Chart
    st.subheader("📊 Failed Login Chart")
    fig, ax = plt.subplots()
    ip_fail.set_index('ip_address')['fail_count'].plot(kind='bar', ax=ax)
    st.pyplot(fig)

    # Risk scoring
    def calculate_risk(row):
        risk = 0
        if row['status'] == 'failed':
            risk += 2
        if row['hour'] < 5:
            risk += 3
        return risk

    df['risk_score'] = df.apply(calculate_risk, axis=1)

    # High risk
    high_risk = df[df['risk_score'] >= 4]

    st.subheader("⚠️ High Risk Activities")
    st.write(high_risk)

else:
    st.warning("⚠️ Please upload a CSV file to continue")