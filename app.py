import streamlit as st
import openai
import google.generativeai as genai

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Property Studio AI",
    page_icon="🏠",
    layout="wide"
)

# --- SECURITY / PASSWORD PROTECTION ---
APP_PASSWORD = st.secrets.get("APP_PASSWORD", "default_pass")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 Property Studio AI")
    user_pass = st.text_input("Enter Password to Access Dashboard:", type="password")
    if st.button("Login"):
        if user_pass == APP_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password. Please try again.")
    st.stop()

# --- SIDEBAR CONFIGURATION ---
st.sidebar.title("⚙️ AI Engine Settings")

# Model Selection Switcher (Gemini is DEFAULT at index 0)
ai_engine = st.sidebar.selectbox(
    "Select AI Model:",
    ["🟢 Google Gemini (Free Tier)", "🔵 OpenAI (GPT-4o Mini)"],
    index=0
)

# API Keys from Secrets
openai_key = st.secrets.get("OPENAI_API_KEY", "")
gemini_key = st.secrets.get("GEMINI_API_KEY", "")

# Unified LLM Generation Function
def generate_real_estate_content(prompt, engine):
    if "Gemini" in engine:
        if not gemini_key:
            st.error("Missing GEMINI_API_KEY in Streamlit Secrets!")
            st.stop()
        
        # Clean API key to prevent whitespace or quote issues
        clean_key = str(gemini_key).strip().strip('"').strip("'")
        genai.configure(api_key=clean_key)
        
        # Active Google Gemini models in order of preference
        gemini_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        errors = []
        
        for model_name in gemini_models:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text
            except Exception as e:
                errors.append(f"{model_name}: {str(e)}")
                continue
                
        # If all models failed, show the specific primary error
        st.error(f"Gemini API Error details: {errors[0] if errors else 'Connection failed'}")
        return None
        
    else: # OpenAI
        if not openai_key:
            st.error("Missing OPENAI_API_KEY in Streamlit Secrets!")
            st.stop()
        try:
            client = openai.OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"OpenAI API Error: {str(e)}")
            return None
            
# --- MAIN DASHBOARD INTERFACE ---
st.title("🏠 Property Studio AI Dashboard")
st.caption(f"Currently active engine: **{ai_engine}**")

# Tabs for tools
tab1, tab2, tab3 = st.tabs(["✍️ Listing Copywriter", "🎬 Video Shot List", "🖼️ Photo Staging Prompts"])

with tab1:
    st.subheader("Property Listing Copywriter")
    col1, col2 = st.columns(2)
    with col1:
        property_type = st.selectbox("Property Type", ["HDB", "Condo", "Landed", "Commercial"])
        location = st.text_input("Location / Project Name", placeholder="e.g. Tengah Garden Residences / Jurong East")
        specs = st.text_input("Specs (Size / Beds / Baths)", placeholder="e.g. 5-room, 1,410 sqft, 11th floor")
    with col2:
        key_features = st.text_area("Key Selling Points", placeholder="Unblocked view, modern renovation, 5 mins to MRT...")
        tone = st.selectbox("Tone of Voice", ["Engaging & Warm", "Luxury & Premium", "Investor-Focused", "Short & Punchy"])

    if st.button("Generate Listing Description", type="primary"):
        if not location:
            st.warning("Please enter a location or project name.")
        else:
            prompt = f"""
            Act as an expert real estate property marketer. Write a high-converting property listing optimized for PropertyGuru and social media.
            
            Property Type: {property_type}
            Location/Project: {location}
            Specifications: {specs}
            Key Features: {key_features}
            Tone: {tone}
            
            Structure the output with:
            1. An attention-grabbing Headline
            2. Highlighting top 3 core selling points (bullet points)
            3. A detailed storytelling walkthrough of the unit
            4. Clear Call to Action for viewing appointments
            """
            with st.spinner("Generating listing with AI..."):
                result = generate_real_estate_content(prompt, ai_engine)
                if result:
                    st.success("Listing Ready!")
                    st.text_area("Copy your description:", value=result, height=350)

with tab2:
    st.subheader("Video Shot List & Script Generator")
    v_type = st.text_input("Video Focus", placeholder="e.g. 4-Bedroom HDB Walkthrough, 60-second Instagram Reel")
    v_highlights = st.text_area("Key Areas / Angles to Film", placeholder="Balcony view, master bedroom walk-in wardrobe, open kitchen...")
    
    if st.button("Generate Shot List & Script"):
        prompt = f"""
        Create a detailed video shot list and voiceover script tailored for real estate video marketing (DJI Pocket / Mobile filming).
        
        Video Focus: {v_type}
        Areas to Feature: {v_highlights}
        
        Provide:
        - Shot # | Scene Description | Camera Movement | Suggested Voiceover / Text Overlay
        Keep it organized sequentially for easy filming and CapCut editing.
        """
        with st.spinner("Creating shot list..."):
            result = generate_real_estate_content(prompt, ai_engine)
            if result:
                st.success("Shot List Ready!")
                st.markdown(result)

with tab3:
    st.subheader("AI Photo Declutter & Staging Prompts")
    p_desc = st.text_area("Describe the current room / photo", placeholder="e.g. Living room with dark wooden floor, cluttered sofa, dim light")
    p_goal = st.selectbox("Transformation Goal", ["Virtual Declutter", "Virtual Staging (Modern Scandinavian)", "Virtual Staging (Luxury Minimalist)", "Brighten & Enhance"])
    
    if st.button("Generate AI Image Edit Prompt"):
        prompt = f"""
        Write a precise image prompt for AI photo staging/decluttering tools (like Photoshop Generative Fill or Midjourney).
        
        Original Room: {p_desc}
        Target Goal: {p_goal}
        
        Provide the exact prompt text to copy-paste into AI image editing tools for realistic property results.
        """
        with st.spinner("Generating prompt..."):
            result = generate_real_estate_content(prompt, ai_engine)
            if result:
                st.success("Prompt Generated!")
                st.code(result)
