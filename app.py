import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import IsolationForest
import mysql.connector
import bcrypt
import random
from datetime import datetime, timedelta
import requests
import os

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Cyber SOC Dashboard",
    layout="wide"
)

# =====================================================
# GLOBAL STYLE
# =====================================================
st.markdown("""
<style>

.stApp{
    background: linear-gradient(135deg,#071426,#0b2a4a);
    color:white;
    font-family:Arial;
}

h1,h2,h3,h4{
    color:#00c6ff;
}

.login-box{
    background:rgba(255,255,255,0.05);
    padding:30px;
    border-radius:15px;
    backdrop-filter:blur(10px);
    width:420px;
    margin:auto;
    margin-top:60px;
    box-shadow:0 0 20px rgba(0,0,0,0.5);
}

.metric-box{
    background:rgba(255,255,255,0.05);
    padding:20px;
    border-radius:12px;
    text-align:center;
}

.stButton > button{
    background:linear-gradient(90deg,#00c6ff,#0072ff);
    color:white;
    border:none;
    border-radius:10px;
    height:45px;
    width:100%;
    font-size:16px;
}

input{
    background:#020617 !important;
    color:white !important;
}

[data-testid="stSidebar"]{
    background:#020617;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# DATABASE CONNECTION
# =====================================================
def connect_db():
    return mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        port=int(os.getenv("MYSQLPORT"))
    )

# =====================================================
# SESSION STATE
# =====================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "role" not in st.session_state:
    st.session_state.role = ""

if "blocked_ips" not in st.session_state:
    st.session_state.blocked_ips = []

# =====================================================
# PASSWORD FUNCTIONS
# =====================================================
def hash_password(password):
    return bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

def verify_password(password, hashed):
    try:
        return bcrypt.checkpw(
            password.encode(),
            hashed.encode()
        )
    except:
        return password == hashed

# =====================================================
# REAL IP
# =====================================================
def get_real_ip():
    try:
        headers = st.context.headers
        ip = headers.get(
            "x-forwarded-for",
            "127.0.0.1"
        )
        return ip.split(",")[0]
    except:
        return "127.0.0.1"

# =====================================================
# SAVE LOGIN LOG
# =====================================================
def save_log(user, status):

    conn = connect_db()
    cursor = conn.cursor()

    ip = get_real_ip()

    cursor.execute("""
        INSERT INTO logs
        (username, ip_address, login_time, status)
        VALUES (%s,%s,%s,%s)
    """, (
        user,
        ip,
        datetime.now(),
        status
    ))

    conn.commit()
    conn.close()

# =====================================================
# CAPTCHA
# =====================================================
def generate_captcha():
    return str(random.randint(1000, 9999))

# =====================================================
# OTP
# =====================================================
def generate_otp():
    return str(random.randint(100000, 999999))

# =====================================================
# LOCATION API
# =====================================================
@st.cache_data
def get_location(ip):

    try:
        res = requests.get(
            f"http://ip-api.com/json/{ip}"
        )

        data = res.json()

        return data.get("lat"), data.get("lon")

    except:
        return None, None

# =====================================================
# FAKE DATA
# =====================================================
def generate_data():

    users = [
        "admin",
        "user1",
        "user2",
        "hacker"
    ]

    ips = [
        "192.168.1.1",
        "10.0.0.5",
        "172.16.0.3",
        "45.33.32.1"
    ]

    status = (
        ["success"] * 8 +
        ["failed"] * 2
    )

    data = []

    for _ in range(200):

        data.append({

            "username":
            random.choice(users),

            "ip_address":
            random.choice(ips),

            "login_time":
            datetime.now()
            - timedelta(
                minutes=random.randint(1, 5000)
            ),

            "status":
            random.choice(status)
        })

    return pd.DataFrame(data)

# =====================================================
# ADMIN PANEL
# =====================================================
def admin_panel():

    st.subheader("👑 Admin Panel")

    conn = connect_db()

    users = pd.read_sql(
        "SELECT username, role FROM users",
        conn
    )

    logs_df = pd.read_sql(
        "SELECT * FROM logs ORDER BY login_time DESC",
        conn
    )

    st.write("### 👤 Users")
    st.dataframe(users)

    delete_user = st.text_input(
        "Delete Username",
        key="delete_user_input"
    )

    if st.button(
        "Delete User",
        key="delete_user_btn"
    ):

        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM users WHERE username=%s",
            (delete_user,)
        )

        conn.commit()

        st.success("User Deleted")

    st.write("### 📜 Login Logs")
    st.dataframe(logs_df)

    conn.close()

# =====================================================
# AUTH SYSTEM
# =====================================================
def auth():

    st.markdown(
        "<div class='login-box'>",
        unsafe_allow_html=True
    )

    st.title("🔐 Cyber SOC Login")

    menu = st.sidebar.selectbox(
        "Menu",
        [
            "Login",
            "Register",
            "Reset Password"
        ]
    )

    conn = connect_db()
    cursor = conn.cursor()

    # =================================================
    # REGISTER
    # =================================================
    if menu == "Register":

        username = st.text_input(
            "Username",
            key="reg_user"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="reg_pass"
        )

        if st.button(
            "Register",
            key="register_btn"
        ):

            if not username or not password:
                st.error("All fields required")
                return

            hashed = hash_password(password)

            cursor.execute("""
                INSERT INTO users
                (username,password,role)
                VALUES (%s,%s,%s)
            """, (
                username,
                hashed,
                "user"
            ))

            conn.commit()

            st.success("User Registered")

    # =================================================
    # LOGIN
    # =================================================
    elif menu == "Login":

        username = st.text_input(
            "Username",
            key="login_user"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_pass"
        )

        # CAPTCHA
        if "captcha" not in st.session_state:
            st.session_state.captcha = generate_captcha()

        st.write(
            "Captcha:",
            st.session_state.captcha
        )

        captcha_input = st.text_input(
            "Enter Captcha",
            key="captcha_input"
        )

        ip = get_real_ip()

        # BLOCKED IP
        if ip in st.session_state.blocked_ips:
            st.error("🚫 Your IP is blocked")
            st.stop()

        # LOGIN BUTTON
        if st.button(
            "Login",
            key="login_btn"
        ):

            if not username or not password:
                st.error("All fields required")
                return

            if captcha_input != st.session_state.captcha:
                st.error("Wrong Captcha")
                return

            cursor.execute("""
                SELECT password, role
                FROM users
                WHERE username=%s
            """, (username,))

            data = cursor.fetchone()

            if data:

                stored_password, role = data

                valid = verify_password(
                    password,
                    stored_password
                )

                if valid:

                    otp = generate_otp()

                    st.session_state.otp = otp
                    st.session_state.temp_user = username
                    st.session_state.temp_role = role

                    st.warning(
                        f"OTP (Demo): {otp}"
                    )

                else:
                    save_log(username, "failed")
                    st.error("Wrong Password")

            else:
                save_log(username, "failed")
                st.error("User Not Found")

        # OTP VERIFY
        if "otp" in st.session_state:

            entered_otp = st.text_input(
                "Enter OTP",
                key="otp_input"
            )

            if st.button(
                "Verify OTP",
                key="verify_otp_btn"
            ):

                if entered_otp == st.session_state.otp:

                    st.session_state.logged_in = True

                    st.session_state.role = (
                        st.session_state.temp_role
                    )

                    save_log(
                        st.session_state.temp_user,
                        "success"
                    )

                    del st.session_state.otp

                    st.success("Login Successful")

                    st.rerun()

                else:
                    st.error("Wrong OTP")

    # =================================================
    # RESET PASSWORD
    # =================================================
    elif menu == "Reset Password":

        username = st.text_input(
            "Username",
            key="reset_user"
        )

        if st.button(
            "Send OTP",
            key="send_otp_btn"
        ):

            otp = generate_otp()

            st.session_state.reset_otp = otp
            st.session_state.reset_user = username

            st.warning(
                f"Reset OTP: {otp}"
            )

        if "reset_otp" in st.session_state:

            entered_otp = st.text_input(
                "Enter OTP",
                key="reset_otp_input"
            )

            new_password = st.text_input(
                "New Password",
                type="password",
                key="new_pass_input"
            )

            if st.button(
                "Update Password",
                key="update_pass_btn"
            ):

                if entered_otp == st.session_state.reset_otp:

                    hashed = hash_password(
                        new_password
                    )

                    cursor.execute("""
                        UPDATE users
                        SET password=%s
                        WHERE username=%s
                    """, (
                        hashed,
                        st.session_state.reset_user
                    ))

                    conn.commit()

                    st.success("Password Updated")

                else:
                    st.error("Wrong OTP")

    conn.close()

# =====================================================
# DASHBOARD
# =====================================================
def dashboard():

    st.title("💻 Cybersecurity SOC Dashboard")

    # =================================================
    # SIDEBAR
    # =================================================
    st.sidebar.title("⚙️ Controls")

    if st.sidebar.button(
        "Logout",
        key="logout_btn"
    ):

        st.session_state.logged_in = False
        st.rerun()

    # =================================================
    # CSV UPLOAD
    # =================================================
    file = st.sidebar.file_uploader(
        "Upload CSV",
        type=["csv"]
    )

    if file:
        df = pd.read_csv(file)
    else:
        df = generate_data()

    # =================================================
    # PROCESS DATA
    # =================================================
    df["login_time"] = pd.to_datetime(
        df["login_time"]
    )

    df["hour"] = df["login_time"].dt.hour
    df["date"] = df["login_time"].dt.date

    # =================================================
    # TABS
    # =================================================
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dashboard",
        "📜 Logs",
        "💀 Threat Intel",
        "💣 Attack Simulation"
    ])

    # =================================================
    # TAB 1 DASHBOARD
    # =================================================
    with tab1:

        st.subheader("📊 Top Metrics")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Total Logs",
            len(df)
        )

        c2.metric(
            "Failed Logins",
            len(df[df["status"] == "failed"])
        )

        c3.metric(
            "Users",
            df["username"].nunique()
        )

        c4.metric(
            "Blocked IPs",
            len(st.session_state.blocked_ips)
        )

        # ALERTS
        st.subheader("🚨 Security Alerts")

        failed = df[df["status"] == "failed"]

        count_ip = failed.groupby(
            "ip_address"
        ).size()

        for ip, c in count_ip.items():

            if c > 10:

                st.error(
                    f"{ip} BLOCKED ({c} attempts)"
                )

                if ip not in st.session_state.blocked_ips:
                    st.session_state.blocked_ips.append(ip)

            elif c >= 5:

                st.warning(
                    f"{ip} Suspicious ({c} attempts)"
                )

        # =================================================
        # CHARTS
        # =================================================
        col1, col2 = st.columns(2)

        with col1:

            top_ips = (
                failed.groupby("ip_address")
                .size()
                .reset_index(name="count")
            )

            fig_bar = px.bar(
                top_ips,
                x="ip_address",
                y="count",
                color="count",
                title="Top Failed Login IPs",
                template="plotly_dark"
            )

            st.plotly_chart(
                fig_bar,
                use_container_width=True
            )

        with col2:

            fig_pie = px.pie(
                df,
                names=["Brute Force","SQL Injection","Access","Suspicious"],
                title="Anomalies by Type",
                template="plotly_dark"
            )

            st.plotly_chart(
                fig_pie,
                use_container_width=True
            )

        # =================================================
        # LOGIN ACTIVITY GRAPH
        # =================================================
        st.subheader("📈 Login Activity")

        activity = (
            df.groupby("date")
            .size()
            .reset_index(name="logins")
        )
        # CREATE VARIABLES FIRST
        dates = activity["date"]
        logs = activity["logins"]
        
        # TREND LINE
        anomaly = logs.rolling(
            window=2,
            min_periods=1
        ).mean()
        
        # CREATE FIGURE
        fig = go.Figure()
        
        # LOG GRAPH
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=logs,
                mode="lines+markers",
                name="Logs"
            )
        )

        # TREND GRAPH
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=anomaly,
                mode="lines",
                name="Trend"
            )
        )
        # LAYOUT
        fig.update_layout(
            template="plotly_dark",
            title="Login Trend Analysis",
            height=400
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # =================================================
        # HEATMAP
        # =================================================
        st.subheader("🔥 Heatmap")

        heatmap = df.groupby(
            ["hour", "status"]
        ).size().unstack(fill_value=0)

        fig_heat = px.imshow(
            heatmap,
            aspect="auto",
            template="plotly_dark"
        )

        st.plotly_chart(
            fig_heat,
            use_container_width=True
        )

        # =================================================
        # ANOMALY DETECTION
        # =================================================
        st.subheader("🤖 Anomaly Detection")

        df["is_failed"] = (
            df["status"] == "failed"
        ).astype(int)

        model = IsolationForest(
            contamination=0.1,
            random_state=42
        )

        df["anomaly"] = model.fit_predict(
            df[["hour", "is_failed"]]
        )

        st.dataframe(
            df[df["anomaly"] == -1]
        )

        # =================================================
        # RECENT TABLE
        # =================================================
        st.subheader("📋 Recent Logs")
        activity = (
            df.groupby("date")
            .size()
            .reset_index(name="logins")
        )

        # IMPORTANT
        rows = min(len(activity ),10)
        recent_df = pd.DataFrame({
            "Time": activity["date"].tail(rows).astype(str).tolist(),
            "IP": [f"192.168.1.{i}" for i in range(rows)],
            "Event": random.choices(
                ["Login Fail", "SQL Attack", "Access"],
                k=rows
            ),
            "Severity": random.choices(
                ["Low", "Medium", "High"],
                k=rows
            )
        })

        st.dataframe(
            recent_df,
            use_container_width=True
        )

    # =================================================
    # TAB 2 LOGS
    # =================================================
    with tab2:

        st.subheader("📜 Real Time Logs")

        logs_df = pd.read_sql(
            "SELECT * FROM logs ORDER BY login_time DESC",
            connect_db()
        )

        search = st.text_input(
            "Search Logs",
            key="search_logs"
        )

        if search:

            logs_df = logs_df[
                logs_df.astype(str).apply(
                    lambda row:
                    row.str.contains(
                        search,
                        case=False
                    ).any(),
                    axis=1
                )
            ]

        st.dataframe(logs_df)

    # =================================================
    # TAB 3 THREAT INTEL
    # =================================================
    with tab3:

        st.subheader("💀 Threat Intelligence")

        anomalies = df[df["anomaly"] == -1]

        st.dataframe(anomalies)

        # MAP
        st.subheader("🌍 Attack Map")

        loc_data = []

        for ip in df["ip_address"].unique():

            lat, lon = get_location(ip)

            if lat and lon:

                loc_data.append({
                    "lat": lat,
                    "lon": lon
                })

        if loc_data:
            st.map(pd.DataFrame(loc_data))

    # =================================================
    # TAB 4 ATTACK SIMULATION
    # =================================================
    with tab4:

        st.subheader("💣 Attack Simulation")

        attack = st.selectbox(
            "Attack Type",
            [
                "Brute Force",
                "DDoS",
                "SQL Injection"
            ]
        )

        if st.button(
            "Run Attack",
            key="attack_btn"
        ):

            for _ in range(20):
                save_log(
                    "hacker",
                    "failed"
                )

            st.error(
                f"{attack} Attack Simulated"
            )

    # =================================================
    # ADMIN PANEL
    # =================================================
    if st.session_state.role == "admin":
        admin_panel()

    # =================================================
    # DOWNLOAD REPORT
    # =================================================
    st.download_button(
        "📥 Download Report",
        df.to_csv(index=False).encode("utf-8"),
        "report.csv",
        key="download_btn"
    )

# =====================================================
# MAIN
# =====================================================
if not st.session_state.logged_in:
    auth()
else:
    dashboard()