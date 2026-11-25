import os
import uuid
import requests
import streamlit as st

# API_URL = "http://127.0.0.1:8000/api"
API_URL=os.getenv("API_URL","http://127.0.0.1:8000/api")

os.chdir(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="交易所文档QA助手",
    page_icon="🥺",
    layout="wide"
)

st.title("😊交易所文档读取 QA 助手")


# =========================
# 1. 初始化 Session State
# =========================

defaults = {
    "access_token": None,
    "current_user": None,
    "thread_id": str(uuid.uuid4()),
    "conversation_id": None,
    "messages": [],
    "conversations": []
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================
# 2. 统一 API 请求
# =========================

def api_request(method, endpoint, **kwargs):

    headers = kwargs.pop("headers", {}).copy()

    if st.session_state.access_token:
        headers["Authorization"] = (
            f"Bearer {st.session_state.access_token}"
        )

    response = requests.request(
        method,
        f"{API_URL}{endpoint}",
        headers=headers,
        timeout=kwargs.pop("timeout", 60),
        **kwargs
    )

    # Token 失效，清除登录状态
    if response.status_code == 401:

        st.session_state.access_token = None
        st.session_state.current_user = None
        st.session_state.messages = []
        st.session_state.conversations = []
        st.session_state.conversation_id = None
        st.session_state.thread_id = str(uuid.uuid4())

        st.rerun()

    response.raise_for_status()

    return response


def show_error(error):

    if isinstance(error, requests.HTTPError):
        try:
            detail = error.response.json().get("detail", str(error))
        except (ValueError, AttributeError):
            detail = str(error)

        st.error(f"请求失败：{detail}")

    else:
        st.error(f"请求失败：{error}")


# =========================
# 3. 登录 / 注册
# =========================

if st.session_state.access_token is None:

    st.subheader("🔐 用户认证")

    tab1, tab2 = st.tabs(["登录", "注册"])

    # -------- 登录 --------

    with tab1:

        with st.form("login_form"):

            email = st.text_input("邮箱")
            password = st.text_input(
                "密码",
                type="password"
            )

            login_submit = st.form_submit_button(
                "登录",
                use_container_width=True
            )

        if login_submit:

            if not email or not password:
                st.warning("请输入邮箱和密码")

            else:
                try:
                    response = requests.post(
                        f"{API_URL}/auth/login",
                        params={
                            "email": email,
                            "password": password
                        },
                        timeout=30
                    )

                    response.raise_for_status()

                    data = response.json()

                    st.session_state.access_token = (
                        data["access_token"]
                    )

                    # 获取当前用户信息
                    response = api_request(
                        "GET",
                        "/auth/me"
                    )

                    st.session_state.current_user = (
                        response.json()
                    )

                    st.session_state.thread_id = str(uuid.uuid4())

                    st.success("登录成功！")
                    st.rerun()

                except requests.RequestException as e:

                    st.session_state.access_token = None
                    st.session_state.current_user = None

                    show_error(e)

    # -------- 注册 --------

    with tab2:

        with st.form("register_form"):

            user_name = st.text_input("用户名")
            email = st.text_input("邮箱")
            password = st.text_input(
                "密码",
                type="password"
            )

            register_submit = st.form_submit_button(
                "注册",
                use_container_width=True
            )

        if register_submit:

            if not user_name or not email or not password:
                st.warning("请填写完整的注册信息")

            else:
                try:
                    response = requests.post(
                        f"{API_URL}/auth/register",
                        params={
                            "user_name": user_name,
                            "email": email,
                            "password": password
                        },
                        timeout=30
                    )

                    response.raise_for_status()

                    st.success("注册成功，请切换到登录页面！")

                except requests.RequestException as e:
                    show_error(e)

    st.stop()


# =========================
# 4. 获取历史会话列表
# =========================

def get_conversations():

    response = api_request(
        "GET",
        "/conversation/list"
    )

    return response.json()


# =========================
# 5. 加载指定会话
# =========================

def load_conversation(conversation_id, thread_id):

    response = api_request(
        "GET",
        "/messages/check",
        params={
            "conversation_id": conversation_id
        }
    )

    data = response.json()

    st.session_state.messages = [
        {
            "role": msg["role"],
            "content": msg["content"]
        }
        for msg in data
    ]

    st.session_state.conversation_id = conversation_id
    st.session_state.thread_id = thread_id


# =========================
# 6. 新建会话
# =========================

def new_conversation():

    st.session_state.messages = []
    st.session_state.conversation_id = None
    st.session_state.thread_id = str(uuid.uuid4())


# =========================
# 7. 删除指定会话
# =========================

def delete_conversation(conversation_id):

    api_request(
        "DELETE",
        "/conversation/clear",
        params={
            "conversation_id": conversation_id
        }
    )

    # 如果删除的是当前会话，重置前端状态
    if st.session_state.conversation_id == conversation_id:
        new_conversation()


# =========================
# 8. 侧边栏：用户与会话管理
# =========================

with st.sidebar:

    st.markdown("## 😎 关于助手")

    st.markdown("""
    这是一个基于 **RAG + LangGraph** 的交易所文档问答助手。

    ### 功能：
    - 读取交易所相关文档
    - 追溯文档来源
    - 查询深交所、上交所公告
    - 持久化保存聊天记录
    """)

    st.markdown("---")

    # 当前登录用户
    current_user = st.session_state.current_user

    st.markdown("### 👤 当前用户")

    st.caption(f"用户名：{current_user.get('username', '')}")
    st.caption(f"邮箱：{current_user.get('email', '')}")

    if st.button("退出登录", use_container_width=True):

        st.session_state.access_token = None
        st.session_state.current_user = None
        st.session_state.messages = []
        st.session_state.conversations = []
        st.session_state.conversation_id = None
        st.session_state.thread_id = str(uuid.uuid4())

        st.rerun()

    st.markdown("---")

    # 新建会话
    if st.button("➕ 新建会话", use_container_width=True):

        new_conversation()
        st.rerun()

    st.markdown("### 📚 历史会话")

    # 获取当前用户的历史会话
    try:
        st.session_state.conversations = get_conversations()

    except requests.RequestException as e:
        show_error(e)

    # 展示历史会话
    for item in st.session_state.conversations:

        conversation_id = item["id"]
        title = item.get("title") or "新建会话"
        thread_id = item["thread_id"]

        col1, col2 = st.columns([4, 1])

        with col1:

            button_label = (
                f"👉 {title}"
                if st.session_state.conversation_id == conversation_id
                else title
            )

            if st.button(
                button_label,
                key=f"conversation_{conversation_id}",
                use_container_width=True
            ):

                try:
                    load_conversation(
                        conversation_id,
                        thread_id
                    )

                    st.rerun()

                except requests.RequestException as e:
                    show_error(e)

        with col2:

            if st.button(
                "🗑️",
                key=f"delete_{conversation_id}"
            ):

                try:
                    delete_conversation(conversation_id)
                    st.rerun()

                except requests.RequestException as e:
                    show_error(e)

    st.markdown("---")

    st.caption(
        f"当前会话 ID：{st.session_state.conversation_id}"
    )

    # 清空当前对话
    if st.button(
        "🫠 清空当前对话",
        use_container_width=True
    ):

        conversation_id = st.session_state.conversation_id

        if conversation_id is not None:

            try:
                delete_conversation(conversation_id)

            except requests.RequestException as e:
                show_error(e)
                st.stop()

        else:
            new_conversation()

        st.rerun()

    st.markdown("---")

    st.caption("🤓 提示：问题越具体，回答越精准")


# =========================
# 9. 显示聊天历史
# =========================

for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):
        st.write(msg["content"])


# =========================
# 10. 发送消息
# =========================

if question := st.chat_input("请输入您的问题..."):

    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):

        with st.spinner("思考中..."):

            try:

                params = {}

                # 已有会话时携带 conversation_id
                if st.session_state.conversation_id is not None:

                    params["conversation_id"] = (
                        st.session_state.conversation_id
                    )

                response = api_request(
                    "POST",
                    "/chat/qa",
                    params=params,
                    json={
                        "question": question,
                        "thread_id": st.session_state.thread_id
                    },
                    timeout=300
                )

                data = response.json()

                answer = data["answer"]

                # 更新当前会话 ID
                st.session_state.conversation_id = (
                    data["conversation_id"]
                )

                st.write(answer)

                # 更新前端聊天记录
                st.session_state.messages.extend([
                    {
                        "role": "user",
                        "content": question
                    },
                    {
                        "role": "assistant",
                        "content": answer
                    }
                ])

                # 刷新历史会话列表
                st.session_state.conversations = get_conversations()

            except requests.RequestException as e:
                show_error(e)
