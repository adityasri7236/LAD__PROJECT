import streamlit as st
import base64

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(page_title="Cyber SOC Login", layout="wide")

# -------------------------
# BACKGROUND IMAGE FUNCTION
# -------------------------
def set_bg():
    with open("bg.png", "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()

    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{b64}");
        background-size: cover;
    }}
    </style>
    """, unsafe_allow_html=True)

# 👉 put your image as bg.png
# set_bg()

# -------------------------
# CUSTOM CSS (MATCH DESIGN)
# -------------------------
st.markdown("""
<style>

.main-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 90vh;
}

.login-box {
    background: rgba(255,255,255,0.05);
    padding: 40px;
    border-radius: 15px;
    width: 400px;
    backdrop-filter: blur(10px);
    box-shadow: 0 0 20px rgba(0,0,0,0.5);
}

.title {
    font-size: 28px;
    font-weight: bold;
    color: white;
    text-align: center;
}

.subtitle {
    color: #aaa;
    text-align: center;
    margin-bottom: 20px;
}

input {
    width: 100%;
    padding: 12px;
    margin-top: 10px;
    border-radius: 10px;
    border: none;
    background: rgba(255,255,255,0.1);
    color: white;
}

button {
    width: 100%;
    padding: 12px;
    margin-top: 20px;
    border-radius: 10px;
    border: none;
    background: linear-gradient(to right, #1e90ff, #007bff);
    color: white;
    font-size: 16px;
}

</style>
""", unsafe_allow_html=True)

# -------------------------
# UI LAYOUT
# -------------------------
col1, col2 = st.columns([1.2, 1])

with col1:
    st.markdown("""
    <h1 style='color:white;'>🔐 Cyber SOC</h1>
    <p style='color:gray;'>DASHBOARD</p>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="login-box">
        <div class="title">Welcome Back!</div>
        <div class="subtitle">Sign in to continue</div>
    </div>
    """, unsafe_allow_html=True)

    username = st.text_input("Username / Email")
    password = st.text_input("Password", type="password")

    colA, colB = st.columns(2)
    with colA:
        remember = st.checkbox("Remember Me")
    with colB:
        st.markdown("<p style='color:#4da6ff; margin-top:30px;'>Forgot Password?</p>", unsafe_allow_html=True)

    if st.button("Login"):
        if username == "admin" and password == "admin":
            st.success("Login Successful")
        else:
            st.error("Invalid Credentials")

    st.markdown("---")
    st.button("Login with OTP")

    st.markdown("<p style='color:gray;'>Don't have an account? <span style='color:#4da6ff;'>Register</span></p>", unsafe_allow_html=True)