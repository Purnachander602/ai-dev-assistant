import streamlit as st
from groq import Groq
from pymongo import MongoClient
from datetime import datetime, timedelta
import bcrypt
import json
import uuid
import pandas as pd

# ----------------------------------
# PAGE CONFIG
# ----------------------------------
st.markdown('<h1 class="main-title">AI Developer Assistant</h1>', unsafe_allow_html=True)
st.markdown("""
<style>

/* ===== FONT ===== */
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap');

/* ===== GLOBAL ===== */
html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
    background: linear-gradient(135deg, #fef9c3, #d1fae5, #dbeafe);
    color: #1e293b;
}

/* ===== CONTAINER ===== */
.block-container {
    padding-top: 2rem;
    padding-bottom: 140px;
    max-width: 900px;
    margin: auto;
}

/* ===== TITLE ===== */
h1 {
    font-size: 36px;
    font-weight: 600;
    text-align: center;

    background: linear-gradient(90deg, #facc15, #22c55e, #3b82f6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e5e7eb;
}

/* ===== CHAT ROW FIX (IMPORTANT) ===== */
[data-testid="stChatMessage"] {
    display: flex !important;
    width: 100%;
    margin-bottom: 12px;
}

/* ===== MESSAGE BOX ===== */
[data-testid="stChatMessage"] > div {
    max-width: 75%;
    padding: 14px;
    border-radius: 18px;
}

/* ===== USER MESSAGE (RIGHT) ===== */
[data-testid="stChatMessage"]:nth-of-type(odd) {
    justify-content: flex-end;
}

[data-testid="stChatMessage"]:nth-of-type(odd) > div {
    background: linear-gradient(135deg, #3b82f6, #06b6d4);
    color: white;
}

/* ===== AI MESSAGE (LEFT) ===== */
[data-testid="stChatMessage"]:nth-of-type(even) {
    justify-content: flex-start;
}

[data-testid="stChatMessage"]:nth-of-type(even) > div {
    background: #ffffff;
    color: #1e293b;
    border: 1px solid #e5e7eb;
}

/* ===== INPUT BOX ===== */
div[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 25px;
    left: 50%;
    transform: translateX(-50%);

    width: 900px;
    max-width: 90%;

    background: #ffffff;
    border-radius: 30px;
    padding: 12px 18px;

    border: 2px solid transparent;

    background-image: linear-gradient(#ffffff, #ffffff),
                      linear-gradient(90deg, #facc15, #22c55e, #3b82f6);
    background-origin: border-box;
    background-clip: padding-box, border-box;

    box-shadow: 0 10px 25px rgba(0,0,0,0.08);
}

/* ===== INPUT TEXT FIX ===== */
div[data-testid="stChatInput"] textarea {
    background: #ffffff !important;
    color: #1e293b !important;
    border: none !important;
    outline: none !important;
    font-size: 15px !important;
}

/* ===== PLACEHOLDER ===== */
div[data-testid="stChatInput"] textarea::placeholder {
    color: #94a3b8 !important;
}

/* ===== BUTTONS ===== */
.stButton button {
    background: linear-gradient(135deg, #facc15, #22c55e, #3b82f6);
    color: white;
    border-radius: 12px;
    border: none;
    padding: 8px 14px;
    font-weight: 500;
    transition: 0.25s;
}

.stButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 15px rgba(59,130,246,0.3);
}

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar {
    width: 6px;
}
::-webkit-scrollbar-thumb {
    background: #93c5fd;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)
# ----------------------------------
# DATABASE
# ----------------------------------
client_db = MongoClient(st.secrets["MONGO_URI"])
db = client_db["ai_dev_assistant"]
users_collection = db["users"]
history_collection = db["history"]
chats_collection = db["chats"]

# ----------------------------------
# ADMIN INIT
# ----------------------------------
if not users_collection.find_one({"role": "admin"}):
    users_collection.insert_one({
        "email": "admin@gmail.com",
        "password": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode(),
        "role": "admin"
    })

# ----------------------------------
# GROQ
# ----------------------------------
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ----------------------------------
# SESSION INIT
# ----------------------------------
defaults = {
    "logged_in": False,
    "role": "user",
    "user_email": "",
    "messages": [],
    "current_chat_id": None
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ----------------------------------
# AUTH
# ----------------------------------
def login(email, password):
    user = users_collection.find_one({"email": email})
    if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
        return user
    return None

def signup(email, password):
    if users_collection.find_one({"email": email}):
        return False
    users_collection.insert_one({
        "email": email,
        "password": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
        "role": "user"
    })
    return True

# ----------------------------------
# CHAT DB
# ----------------------------------
def create_chat():
    chat_id = str(uuid.uuid4())
    chats_collection.insert_one({
        "chat_id": chat_id,
        "user_email": st.session_state.user_email,
        "name": "New Chat",
        "created_at": datetime.now()
    })
    return chat_id

def load_chat(chat_id):
    st.session_state.messages = []
    chats = history_collection.find({
        "chat_id": chat_id,
        "user_email": st.session_state.user_email
    }).sort("time", 1)

    for chat in chats:
        st.session_state.messages.append({
            "role": chat["role"],
            "content": chat["message"]
        })

def save_message(chat_id, role, message):
    history_collection.insert_one({
        "chat_id": chat_id,
        "user_email": st.session_state.user_email,
        "role": role,
        "message": message,
        "time": datetime.now()
    })

# ----------------------------------
# AUTH UI
# ----------------------------------
if not st.session_state.logged_in:
    st.title("")

    choice = st.radio("Choose Option", ["Login", "Signup"], horizontal=True)
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if choice == "Login":
        if st.button("Login"):
            user = login(email, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.role = user["role"]
                st.session_state.user_email = user["email"]

                chat = chats_collection.find_one(
                    {"user_email": user["email"]},
                    sort=[("created_at", -1)]
                )

                st.session_state.current_chat_id = chat["chat_id"] if chat else create_chat()
                load_chat(st.session_state.current_chat_id)
                st.rerun()
            else:
                st.error("Invalid credentials")

    else:
        if st.button("Signup"):
            if signup(email, password):
                st.success("Account created")
            else:
                st.error("User exists")

# ----------------------------------
# MAIN APP
# ----------------------------------
else:
    st.title("")

    # SIDEBAR
    with st.sidebar:
        st.write(f"👤 {st.session_state.user_email}")

        if st.button("➕ New Chat"):
            st.session_state.current_chat_id = create_chat()
            st.session_state.messages = []
            st.rerun()

        chats = list(chats_collection.find(
            {"user_email": st.session_state.user_email}
        ).sort("created_at", -1))

        for chat in chats:
            if st.button(chat["name"], key=chat["chat_id"]):
                st.session_state.current_chat_id = chat["chat_id"]
                load_chat(chat["chat_id"])
                st.rerun()

        if st.button("🚪 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # ----------------------------------
    # ADMIN DASHBOARD + ANALYTICS
    # ----------------------------------
    if st.session_state.role == "admin":
        st.subheader("🛠 Admin Dashboard")

        # ---- USER MANAGEMENT ----
        search = st.text_input("🔍 Search User")
        query = {}
        if search:
            query["email"] = {"$regex": search, "$options": "i"}

        users = list(users_collection.find(query))
        st.write(f"Total Users: {len(users)}")

        for user in users:
            col1, col2, col3 = st.columns([4, 2, 2])
            with col1: st.write(user["email"])
            with col2: st.write(user.get("role", "user"))
            with col3:
                if user["role"] != "admin":
                    if st.button("❌ Delete", key=str(user["_id"])):
                        users_collection.delete_one({"_id": user["_id"]})
                        st.rerun()
                else:
                    st.write("🔒 Admin")

        # ---- ANALYTICS ----
        st.subheader("📊 Analytics")

        all_messages = list(history_collection.find({}))
        if all_messages:
            df = pd.DataFrame(all_messages)

            # Messages per day
            df["date"] = pd.to_datetime(df["time"]).dt.date
            msgs_per_day = df.groupby("date").size()

            st.line_chart(msgs_per_day)

            # Role distribution
            role_counts = df["role"].value_counts()
            st.bar_chart(role_counts)

            # Active users
            active_users = df["user_email"].nunique()
            st.metric("Active Users", active_users)

            # Total messages
            st.metric("Total Messages", len(df))

        else:
            st.info("No analytics data available")

        # ---- EXPORT ----
        if st.button("💾 Export All Messages"):
            df = pd.DataFrame(all_messages)
            csv = df.to_csv(index=False)
            st.download_button("Download CSV", csv, "messages.csv")

    # ----------------------------------
    # CHAT UI
    # ----------------------------------
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Ask coding question...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        save_message(st.session_state.current_chat_id, "user", prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=st.session_state.messages
                    )
                    answer = response.choices[0].message.content
                    st.markdown(answer)
                except:
                    answer = "Error occurred"
                    st.error(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})
        save_message(st.session_state.current_chat_id, "assistant", answer)

        st.rerun()