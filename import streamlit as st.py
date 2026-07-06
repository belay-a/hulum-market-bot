import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="የኢትዮጵያ AI", page_icon="🤖", layout="centered")

st.title("🤖 የኢትዮጵያ AI")
st.caption("በStreamlit የተገነባ የአማርኛ የውይይት መድረክ")

API_KEY = "AIzaSyAio8f3jjzsbuvlaXQVCY-KwPdI5URNlKw"

@st.cache_resource
def initialize_ai_chat():
    try:
        client = genai.Client(api_key=API_KEY)
        google_search_tool = types.Tool(google_search=types.GoogleSearch())
        
        config = types.GenerateContentConfig(
            system_instruction=(
                "አንተ ሁልጊዜ ወቅታዊ መረጃዎችን ማግኘት የምትችል፣ አጋዥ እና በጣም ጎበዝ የኢትዮጵያ AI ረዳት ነህ። "
                "ስለ ዓለም አዳዲስና ወቅታዊ መረጃዎች፣ ዜናዎች ወይም ሰዓት ተኮር ነገሮች ስትጠየቅ የተሰጠህን የGoogle Search መሣሪያ በመጠቀም "
                "ትክክለኛውን መረጃ ፈልገህ በግልጽ አማርኛ መልስ።"
            ),
            tools=[google_search_tool],
            temperature=0.5,
        )
        return client.chats.create(model="gemini-2.5-flash", config=config)
    except Exception as e:
        st.error(f"AIውን ማስጀመር አልተቻለም፦ {e}")
        return None

chat = initialize_ai_chat()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if chat and (user_query := st.chat_input("እዚህ ላይ ያውሩ...")):
    with st.chat_message("user"):
        st.markdown(user_query)
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    
    with st.chat_message("assistant"):
        try:
            response = chat.send_message(user_query)
            st.markdown(response.text)
            st.session_state.chat_history.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"ስህተት ተከስቷል፦ {e}")