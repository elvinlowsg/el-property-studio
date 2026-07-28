import streamlit as st
from openai import OpenAI

# 1. Simple Password Protection
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🔒 Private Real Estate Studio")
        st.caption("Please enter your password to access your dashboard.")
        user_password = st.text_input("Password", type="password")
        
        if st.button("Unlock Dashboard"):
            if user_password == st.secrets.get("APP_PASSWORD", "defaultpass"):
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect password.")
        return False
    return True

if not check_password():
    st.stop()

# 2. Main Dashboard Layout
st.set_page_config(page_title="Property Studio", layout="wide")
st.title("🏡 My Private Real Estate Command Center")

# Connect to OpenAI API using your stored secret key
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Logout Button in Sidebar
with st.sidebar:
    st.write("Logged in as **Owner**")
    if st.button("Log Out"):
        st.session_state["authenticated"] = False
        st.rerun()

# 3. Workspace Tabs
tab1, tab2, tab3 = st.tabs(["📝 Listing Copywriter", "🎬 Video Script", "🖼️ Photo Staging"])

# TAB 1: LISTING & SOCIAL COPY
with tab1:
    st.header("Listing & Social Media Copywriter")
    details = st.text_area("Paste Unit Specs (e.g., Address, Unit Type, Size, etc):", height=120)
    default_prompt = "You are an expert Singapore real estate marketer. Write a detailed PropertyGuru listing description and a social media caption (FB/IG) with strong hooks, bulleted features, and hashtags including #elvinlowsg."
    system_prompt = st.text_area("Editable Prompt Rule (you can edit this anytime):", value=default_prompt, height=80)
    
    if st.button("Generate Marketing Copy"):
        if details:
            with st.spinner("Writing your copy..."):
                res = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": details}
                    ]
                )
                st.success("Done!")
                st.write(res.choices[0].message.content)

# TAB 2: VIDEO SCRIPT
with tab2:
    st.header("CapCut 2-Column Shot List")
    video_input = st.text_area("Key Selling Points or Room Sequence for Video:", height=100)
    
    if st.button("Generate Video Shot List"):
        if video_input:
            with st.spinner("Creating shot list..."):
                res = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Write a 30-second TikTok/Reels video shot list formatted as a 2-column table: Column 1 = [Visual Action/Camera Movement], Column 2 = [Voiceover / Caption]."},
                        {"role": "user", "content": video_input}
                    ]
                )
                st.success("Done!")
                st.write(res.choices[0].message.content)

# TAB 3: PHOTO DECLUTTER & STAGING PROMPTS
with tab3:
    st.header("Photo Editing & Staging Prompt Studio")
    default_photo_prompt = "Remove all furniture, wall art, and clutter. Maintain architectural room layout, original floor texture, window placements, and ambient lighting. Output clean, bare empty room walls."
    editable_photo_rule = st.text_area("Editable Standard Photo Rule:", value=default_photo_prompt, height=100)
    room_type = st.text_input("Room Description (e.g., Master bedroom with parquet flooring):")
    
    if st.button("Generate AI Image Prompt"):
        if room_type:
            full_prompt = f"{editable_photo_rule} Target Room: {room_type}"
            st.subheader("Your Custom Prompt to copy into ChatGPT / DALL-E:")
            st.code(full_prompt, language="text")
