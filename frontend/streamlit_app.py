import streamlit as st
import requests
import json
from datetime import datetime
import time

API_BASE_URL = "http://localhost:8000/api"

# Page config
st.set_page_config(
    page_title="NSF Graph RAG",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for subtle improvements
st.markdown("""
<style>
    /* App header styling */
    .stApp > header {
        background-color: transparent;
    }

    /* Improve button styling */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    /* Chat message styling */
    .stChatMessage {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 0.5rem;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e0e0e0;
    }

    /* File uploader styling */
    .uploadedFile {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }

    /* Success/Error message styling */
    .stAlert {
        border-radius: 8px;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    if 'token' not in st.session_state:
        st.session_state.token = None
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'conversations' not in st.session_state:
        st.session_state.conversations = []


def login(email, password):
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            data={"username": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.token = data["access_token"]

            user_response = requests.get(
                f"{API_BASE_URL}/auth/me",
                headers={"Authorization": f"Bearer {st.session_state.token}"}
            )
            if user_response.status_code == 200:
                st.session_state.user = user_response.json()
                return True
        return False
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return False


def logout():
    for key in ['token', 'user', 'conversation_id', 'messages', 'conversations']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


def send_message(message):
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        payload = {"message": message}
        if st.session_state.conversation_id:
            payload["conversation_id"] = st.session_state.conversation_id

        response = requests.post(
            f"{API_BASE_URL}/chat/chat",
            json=payload,
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            st.session_state.conversation_id = data["conversation_id"]
            return data["response"]
        else:
            return "Sorry, I encountered an error processing your request."
    except Exception:
        return "Sorry, I'm having trouble connecting right now."


def get_conversations():
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        response = requests.get(
            f"{API_BASE_URL}/chat/conversations",
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []


def load_conversation_messages(conv_id):
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        response = requests.get(
            f"{API_BASE_URL}/chat/conversations/{conv_id}/messages",
            headers=headers
        )
        if response.status_code == 200:
            messages = response.json()
            st.session_state.messages = []
            for msg in messages:
                st.session_state.messages.append({
                    "role": "user",
                    "content": msg["user_message"]
                })
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": msg["ai_response"]
                })
            st.session_state.conversation_id = conv_id
            return True
    except Exception:
        return False


def upload_document(file):
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        files = {"file": (file.name, file, file.type)}

        response = requests.post(
            f"{API_BASE_URL}/documents/upload",
            files=files,
            headers=headers
        )

        return response.status_code == 200
    except Exception:
        return False


def render_login_page():
    # Create three columns for centering
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Logo and title
        st.markdown("<h1 style='text-align: center; color: #1f77b4; margin-bottom: 0;'>🔗 NSF Graph RAG</h1>",
                    unsafe_allow_html=True)
        st.markdown(
            "<p style='text-align: center; color: #666; margin-bottom: 2rem;'>Next Step Foundation Knowledge Assistant</p>",
            unsafe_allow_html=True)

        # Login form container
        with st.container():
            st.markdown(
                "<div style='background-color: #f8f9fa; padding: 2rem; border-radius: 10px; border: 1px solid #e0e0e0;'>",
                unsafe_allow_html=True)

            # Login form
            with st.form("login_form", clear_on_submit=False):
                st.markdown("<h3 style='text-align: center; margin-bottom: 1.5rem;'>Sign In</h3>",
                            unsafe_allow_html=True)

                email = st.text_input(
                    "Email Address",
                    placeholder="Enter your email",
                    label_visibility="visible"
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    label_visibility="visible"
                )

                st.markdown("<br>", unsafe_allow_html=True)

                submitted = st.form_submit_button(
                    "Sign In",
                    use_container_width=True,
                    type="primary"
                )

                if submitted:
                    if email and password:
                        with st.spinner("Signing in..."):
                            if login(email, password):
                                st.success("Login successful! Redirecting...")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Invalid credentials. Please check your email and password.")
                    else:
                        st.error("Please enter both email and password.")

            st.markdown("</div>", unsafe_allow_html=True)

        # Footer
        st.markdown(
            "<p style='text-align: center; color: #999; margin-top: 2rem; font-size: 0.9rem;'>© 2024 Next Step Foundation</p>",
            unsafe_allow_html=True)


def render_sidebar():
    with st.sidebar:
        # User info
        st.markdown("### 👤 User Profile")
        st.info(f"**Email:** {st.session_state.user['email']}\n\n**Role:** {st.session_state.user['role'].title()}")

        # New conversation button
        if st.button("➕ New Conversation", use_container_width=True, type="primary"):
            st.session_state.conversation_id = None
            st.session_state.messages = []
            st.rerun()

        st.divider()

        # Conversations list
        st.markdown("### 💬 Recent Conversations")

        conversations = get_conversations()
        st.session_state.conversations = conversations

        if conversations:
            for conv in conversations[:15]:
                # Create a button for each conversation
                conv_title = conv['title'][:40] + ("..." if len(conv['title']) > 40 else "")
                conv_date = datetime.fromisoformat(conv['created_at'].replace('Z', '+00:00')).strftime("%b %d, %Y")

                if st.button(
                        f"📄 {conv_title}\n_{conv_date}_",
                        key=f"conv_{conv['id']}",
                        use_container_width=True,
                        help=conv['title']
                ):
                    with st.spinner("Loading conversation..."):
                        if load_conversation_messages(conv['id']):
                            st.rerun()
        else:
            st.info("No conversations yet. Start a new one!")

        st.divider()

        # Document upload for admin/staff
        if st.session_state.user['role'] in ['admin', 'staff']:
            st.markdown("### 📁 Document Upload")

            uploaded_file = st.file_uploader(
                "Choose a document",
                type=['pdf', 'docx', 'doc'],
                help="Upload PDF or Word documents to the knowledge base"
            )

            if uploaded_file:
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"📄 {uploaded_file.name}")
                with col2:
                    if st.button("Upload", key="upload_btn", type="secondary"):
                        with st.spinner("Uploading..."):
                            if upload_document(uploaded_file):
                                st.success("✅ Uploaded successfully!")
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("❌ Upload failed")

        st.divider()

        # Logout button
        if st.button("🚪 Sign Out", use_container_width=True, type="secondary"):
            logout()


def render_chat_interface():
    # Header
    st.markdown("## 🔗 NSF Graph RAG")
    st.markdown("Ask questions about Next Step Foundation programs, impact reports, and initiatives.")

    # Chat container
    chat_container = st.container()

    with chat_container:
        # Display messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Type your question here...", key="chat_input"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = send_message(prompt)
            st.markdown(response)

        # Add assistant message to history
        st.session_state.messages.append({"role": "assistant", "content": response})

        # Scroll to bottom
        st.rerun()

    # Welcome message if no messages
    if not st.session_state.messages:
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown("""
                <div style='text-align: center; padding: 3rem; background-color: #f8f9fa; border-radius: 10px; margin-top: 2rem;'>
                    <h3>👋 Welcome to NSF Graph RAG!</h3>
                    <p>I'm here to help you find information about:</p>
                    <ul style='text-align: left; display: inline-block;'>
                        <li>NSF Programs and Initiatives</li>
                        <li>Impact Reports and Statistics</li>
                        <li>Grant Information</li>
                        <li>Community Resources</li>
                    </ul>
                    <p><em>Start by asking a question below!</em></p>
                </div>
                """, unsafe_allow_html=True)


def main():
    # Initialize session state
    init_session_state()

    # Render appropriate page
    if not st.session_state.token:
        render_login_page()
    else:
        # Create layout
        render_sidebar()
        render_chat_interface()


if __name__ == "__main__":
    main()