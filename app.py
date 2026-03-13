import streamlit as st
import ollama

st.set_page_config(page_title="AI Developer Assistant", layout="wide")

st.title("💻 AI Developer Assistant")

# Store chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
prompt = st.chat_input("Ask coding question...")

if prompt:

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):

        response = ollama.chat(
            model="deepseek-coder",
            messages=st.session_state.messages
        )

        answer = response["message"]["content"]

        st.markdown(answer)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )