import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.ensemble import IsolationForest
import mysql.connector
import bcrypt
import random
from datetime import datetime, timedelta
import requests
import base64


# --------------------------
# PAGE CONFIG
# --------------------------
st.set_page_config(page_title="Cyber SOC Dashboard", layout="wide")


def set_bg():
    with open("bg.png", "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()

    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{b64}");
        background-size: cover;
        background-position: center;
    }}
    </style>
    """, unsafe_allow_html=True)

set_bg()

# --------------------------
# GLOBAL STYLE
# --------------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #020617, #0f172a);
    color: white;
}

/* Login Box */
.login-box {
    background: rgba(15, 23, 42, 0.9);
    padding: 40px;
    border-radius: 15px;
    width: 400px;
    margin: auto;
    margin-top: 80px;
    box-shadow: 0 0 40px rgba(0,0,0,0.5);
}

/* Inputs */
input {
    background: #020617 !important;
    color: white !important;
}

/* Button */
.stButton > button {
    width: 100%;
    border-radius: 10px;
    background: linear-gradient(90deg, #2563eb, #3b82f6);
    color: white;
    border: none;
}
</style>
""", unsafe_allow_html=True)

# --------------------------
# DATABASE
# --------------------------
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="aditya",  # change if needed
        database="cyber_db"
    )

# --------------------------
# SESSION
# --------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = ""
if "blocked_ips" not in st.session_state:
    st.session_state.blocked_ips = []  

# --------------------------
# REAL IP
# --------------------------
def get_real_ip():
    try:
        headers = st.context.headers
        ip = headers.get("x-forwarded-for", "127.0.0.1")
        return ip.split(",")[0]
    except:
        return "127.0.0.1"

# --------------------------
# SAVE LOGIN LOG (NEW)
# --------------------------
def save_log(user, status):
    conn = connect_db()
    cursor = conn.cursor()

    ip = get_real_ip()  # demo

    cursor.execute("""
        INSERT INTO logs (username, ip_address, login_time, status)
        VALUES (%s,%s,%s,%s)
    """, (user, ip, datetime.now(), status))

    conn.commit()
    conn.close()
# --------------------------
# CAPTCHA
# --------------------------
def generate_captcha():
    return str(random.randint(1000,9999))


# --------------------------
# OTP
# --------------------------
def generate_otp():
    return str(random.randint(100000,999999))


# --------------------------
# LOCATION API
# --------------------------
@st.cache_data
def get_location(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}")
        data = res.json()
        return data.get("lat"), data.get("lon")
    except:
        return None, None

# --------------------------
# AUTH (HACKER UI)
# --------------------------
def auth():
    st.title("💀 Cyber Login Terminal")
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown("### 🔐 Welcome Back")
    st.write("Login to Cyber SOC Dashboard")

    menu = st.sidebar.selectbox("Menu", ["Login","Register","Reset Password"])

    conn = connect_db()
    cursor = conn.cursor()

    # -------- REGISTER --------
    if menu=="Register":
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")

        if st.button("Register"):
            hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
            cursor.execute("INSERT INTO users (username,password,role) VALUES (%s,%s,%s)",
                           (user,hashed,"user"))
            conn.commit()
            st.success("User Created")

    # -------- LOGIN --------
    elif menu=="Login":
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")

        ip = get_real_ip()
        if ip in st.session_state.blocked_ips:
            st.error("🚫 Your IP is blocked")
            st.stop()

        if st.button("Login"):
            cursor.execute("SELECT password,role FROM users WHERE username=%s",(user,))
            data = cursor.fetchone()

            if data:
                stored, role = data

                try:
                    valid = bcrypt.checkpw(pwd.encode(), stored.encode())
                except:
                    valid = (pwd == stored)

                if valid:
                    otp = generate_otp()
                    st.session_state.otp = otp
                    st.session_state.temp_user = user
                    st.session_state.temp_role = role
                    st.warning(f"OTP (demo): {otp}")
                else:
                    save_log(user,"failed")
                    st.error("Wrong Password ❌")
            else:
                save_log(user,"failed")
                st.error("User Not Found ❌")

    # -------- OTP VERIFY --------
    if "otp" in st.session_state:
        entered = st.text_input("Enter OTP")

        if st.button("Verify OTP"):
            if entered == st.session_state.otp:
                st.session_state.logged_in = True
                st.session_state.role = st.session_state.temp_role
                save_log(st.session_state.temp_user,"success")
                del st.session_state.otp
                st.success("Login Success")
                st.rerun()
            else:
                st.error("Wrong OTP")

    # -------- RESET --------
    elif menu=="Reset Password":
        user = st.text_input("Username")

        if st.button("Send OTP"):
            otp = generate_otp()
            st.session_state.reset_otp = otp
            st.session_state.reset_user = user
            st.warning(f"Reset OTP: {otp}")

    if "reset_otp" in st.session_state:
        otp = st.text_input("Enter OTP")
        new_pass = st.text_input("New Password", type="password")

        if st.button("Update Password"):
            if otp == st.session_state.reset_otp:
                hashed = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt()).decode()
                cursor.execute("UPDATE users SET password=%s WHERE username=%s",
                               (hashed, st.session_state.reset_user))
                conn.commit()
                st.success("Password Updated")
            else:
                st.error("Wrong OTP")

    conn.close()

 

# --------------------------
# FAKE DATA
# --------------------------
def generate_data():
    users = ["admin", "user1", "user2", "hacker"]
    ips = ["192.168.1.1", "10.0.0.5", "172.16.0.3", "45.33.32.1"]

    status = ["success"] * 8 + ["failed"] * 2

    data = []
    for _ in range(200):
        data.append({
            "username": random.choice(users),
            "ip_address": random.choice(ips),
            "login_time": datetime.now() - timedelta(minutes=random.randint(1, 5000)),
            "status": random.choice(status)
        })

    return pd.DataFrame(data)

# --------------------------
# ADMIN PANEL (NEW)
# --------------------------
def admin_panel():
    st.subheader("👑 Admin Panel")

    conn = connect_db()

    users = pd.read_sql("SELECT username, role FROM users", conn)
    logs = pd.read_sql("SELECT * FROM logs ORDER BY login_time DESC", conn)

    st.write("👤 Users")
    st.dataframe(users)

    del_user = st.text_input("Delete Username")
    if st.button("Delete User"):
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username=%s", (del_user,))
        conn.commit()
        st.success("User Deleted")

    st.write("📜 Logs")
    st.dataframe(logs)

    conn.close()

# --------------------------
# DASHBOARD
# --------------------------
def dashboard():
    st.title("💻 Cybersecurity SOC Dashboard")

    # LOGOUT
    if st.sidebar.button("Logout", key="logout_btn"):
        st.session_state.logged_in = False
        st.rerun()

    # LOAD DATA
    file = st.file_uploader("Upload CSV", type=["csv"])

    if file:
        df = pd.read_csv(file)
    else:
        df = generate_data()

    # PROCESS
    df['login_time'] = pd.to_datetime(df['login_time'])
    df['hour'] = df['login_time'].dt.hour
    df['date'] = df['login_time'].dt.date

    # TABS
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📜 Logs", "💀 Threat Intel","💣 Attack" ])

    # ---------------- TAB 1 ----------------
    with tab1:
        st.subheader("📊 Overview")

        c1, c2, c3 = st.columns(3)
        c1.metric("Total", len(df))
        c2.metric("Failed", len(df[df['status']=="failed"]))
        c3.metric("Users", df['username'].nunique())

        # ALERTS
        st.subheader("🚨 Alerts")
        failed = df[df['status']=="failed"]
        count_ip = failed.groupby('ip_address').size()

        for ip, c in count_ip.items():
            if c > 10:
                st.error(f"{ip} BLOCKED")
                if ip not in st.session_state.blocked_ips:
                    st.session_state.blocked_ips.append(ip)

        st.plotly_chart(px.bar(df,x='ip_address',color='status'))

        # GRAPH
        col1, col2 = st.columns(2)

        fig1 = px.bar(
            failed.groupby('ip_address').size().reset_index(name='count'),
            x='ip_address', y='count'
        )
        col1.plotly_chart(fig1, use_container_width=True)

        fig2 = px.pie(df, names='status')
        col2.plotly_chart(fig2, use_container_width=True)

        # LINE
        activity = df.groupby('date').size().reset_index(name='logins')
        st.plotly_chart(px.line(activity, x='date', y='logins'), use_container_width=True)

        # HEATMAP
        heatmap = df.groupby(['hour', 'status']).size().unstack(fill_value=0)
        st.plotly_chart(px.imshow(heatmap), use_container_width=True)

        # ML
        st.subheader("🤖 Anomaly Detection")
        df['is_failed'] = (df['status']=="failed").astype(int)

        model = IsolationForest(contamination=0.1, random_state=42)
        df['anomaly'] = model.fit_predict(df[['hour','is_failed']])

        st.dataframe(df[df['anomaly'] == -1])

    # ---------------- TAB 2 ----------------
    with tab2:
        logs = pd.read_sql("SELECT * FROM logs ORDER BY login_time DESC", connect_db())
        search = st.text_input("Search logs")
        if search:
            logs = logs[logs.astype(str).apply(lambda r: r.str.contains(search,case=False).any(),axis=1)]
        st.dataframe(logs)
    # ---------------- TAB 3 ----------------
    with tab3:
        df['is_failed']=(df['status']=="failed").astype(int)
        model=IsolationForest(contamination=0.1)
        df['anomaly']=model.fit_predict(df[['hour','is_failed']])
        st.dataframe(df[df['anomaly']==-1])

    # --------------TAB 4 -------------------
    with tab4:
        st.subheader("💣 Attack Simulation")

        attack = st.selectbox("Attack Type",["Brute Force","DDoS"])

        if st.button("Run Attack"):
            for i in range(20):
                save_log("hacker","failed")
            st.error("Attack simulated")

    if st.session_state.role=="admin":
        admin_panel()

    
      # MAP
    st.subheader("🌍 Location Map")
    loc_data = []
    for ip in df['ip_address'].unique():
        lat, lon = get_location(ip)
        if lat and lon:
            loc_data.append({"lat": lat, "lon": lon})

    if loc_data:
        st.map(pd.DataFrame(loc_data))

    if st.session_state.role == "admin":
        admin_panel()

    # DOWNLOAD
    st.download_button(
        "Download CSV",
        df.to_csv(index=False).encode('utf-8'),
        "report.csv"
    )

# --------------------------
# MAIN
# --------------------------
if not st.session_state.logged_in:
    auth()
else:
    dashboard()