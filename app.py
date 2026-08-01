import streamlit as st
import openai
import google.generativeai as genai
from PIL import Image
import base64
import io

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

ai_engine = st.sidebar.selectbox(
    "Select AI Model:",
    ["🟢 Google Gemini (Free Tier)", "🔵 OpenAI (GPT-4o Mini)"],
    index=0
)

openai_key = st.secrets.get("OPENAI_API_KEY", "")
gemini_key = st.secrets.get("GEMINI_API_KEY", "")

# Helper to encode PIL Image to Base64 for OpenAI Vision
def encode_image(pil_image):
    buffered = io.BytesIO()
    if pil_image.mode in ("RGBA", "P"):
        pil_image = pil_image.convert("RGB")
    pil_image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- UNIFIED LLM GENERATION FUNCTION ---
def generate_real_estate_content(prompt, engine, image=None):
    if "Gemini" in engine:
        if not gemini_key:
            st.error("Missing GEMINI_API_KEY in Streamlit Secrets!")
            st.stop()
        
        clean_key = str(gemini_key).strip().strip('"').strip("'")
        genai.configure(api_key=clean_key)
        
        # Discover active models
        try:
            available = [
                m.name.replace("models/", "") 
                for m in genai.list_models() 
                if 'generateContent' in m.supported_generation_methods
            ]
            flash_models = [m for m in available if "flash" in m.lower()]
            other_models = [m for m in available if m not in flash_models]
            candidate_models = flash_models + other_models
        except Exception:
            candidate_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        
        errors = []
        for model_name in candidate_models:
            try:
                model = genai.GenerativeModel(model_name)
                # Pass both image and text prompt to Gemini Vision
                contents = [image, prompt] if image else prompt
                response = model.generate_content(contents)
                if response and response.text:
                    return response.text
            except Exception as e:
                errors.append(f"{model_name}: {str(e)}")
                continue
                
        st.error(f"Gemini API Error details: {errors[0] if errors else 'No active Gemini models found.'}")
        return None
        
    else: # OpenAI
        if not openai_key:
            st.error("Missing OPENAI_API_KEY in Streamlit Secrets!")
            st.stop()
        try:
            client = openai.OpenAI(api_key=openai_key)
            
            if image:
                base64_img = encode_image(image)
                messages = [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}
                        }
                    ]
                }]
            else:
                messages = [{"role": "user", "content": prompt}]
                
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"OpenAI API Error: {str(e)}")
            return None

# --- MAIN DASHBOARD INTERFACE ---
st.title("🏠 Property Studio AI Dashboard")
st.caption(f"Currently active engine: **{ai_engine}**")

tab1, tab2, tab3 = st.tabs(["✍️ Listing Copywriter", "🎬 Video Shot List", "🖼️ Photo Staging & Vision Studio"])

# --- TAB 1: LISTING COPYWRITER ---
with tab1:
    st.subheader("Listing Copywriter")
    col1, col2 = st.columns(2)
    with col1:
        property_type = st.selectbox("Property Type", ["HDB", "Condo", "Landed", "Commercial"])
        location = st.text_input("Location / Project Name", placeholder="e.g. 196B Boon Lay Drive / Tengah Garden Residences")
        specs = st.text_input("Specs (Size / Beds / Baths / Floor)", placeholder="e.g. 5-room, 1,410 sqft, 11th floor")
    with col2:
        key_features = st.text_area("Key Selling Points", placeholder="Unblocked view, modern renovation, 5 mins to MRT, move-in condition...")
        tone = st.selectbox("Tone of Voice", ["Engaging & Warm", "Luxury & Premium", "Investor-Focused", "Short & Punchy"])

    if st.button("Generate Listing & Social Posts", type="primary"):
        if not location:
            st.warning("Please enter a location or project name.")
        else:
            prompt = f"""
            Act as an expert real estate property marketer in Singapore. Generate high-converting property marketing copy tailored for PropertyGuru and Social Media.

            Property Details:
            - Property Type: {property_type}
            - Location/Project: {location}
            - Specifications: {specs}
            - Key Features: {key_features}
            - Tone: {tone}

            Output EXACTLY 3 distinct sections using the strict section headers below. Do not include any introductory or concluding conversational text outside these sections.

            ---PROPERTYGURU_HEADLINE---
            Rules for Headline:
            - Length: Must be between 10 and 70 characters total (including spaces).
            - Content: Promote the best feature of the listing.
            - Formatting: Plain text ONLY. Use sentence case with little punctuation marks (exclamation marks, commas, periods).
            Example format: rare high floor 5rm unit near mrt fully renovated unblocked view

            ---PROPERTYGURU_DESCRIPTION---
            Rules for PropertyGuru Description:
            - Thorough description about the property and unit to engage property seekers.
            - Minimum 20 words, maximum 2000 characters limit.
            - Plain text format, clean paragraphs, no complex markdown symbols.

            ---SOCIAL_MEDIA---
            Rules for Social Media (Facebook & Instagram):
            - Formatted cleanly with engaging line breaks and tasteful emojis so it can be copied and pasted directly onto both Facebook and Instagram without any extra formatting needed.
            - Grab property seekers' attention with a strong hook.
            - Highlight key lifestyle and unit selling points.
            - Include a clear Call to Action (CTA) for booking viewing appointments.
            - MANDATORY: Include the personal hashtag #elvinlowsg at the bottom along with 3-5 relevant Singapore real estate hashtags.
            """

            with st.spinner("Generating marketing copy..."):
                result = generate_real_estate_content(prompt, ai_engine)
                
                if result:
                    # Parse LLM response into separate variables
                    if "---PROPERTYGURU_HEADLINE---" in result and "---PROPERTYGURU_DESCRIPTION---" in result and "---SOCIAL_MEDIA---" in result:
                        try:
                            parts = result.split("---PROPERTYGURU_HEADLINE---")[1]
                            headline_part, rest = parts.split("---PROPERTYGURU_DESCRIPTION---")
                            desc_part, social_part = rest.split("---SOCIAL_MEDIA---")
                            
                            st.session_state["pg_headline"] = headline_part.strip()
                            st.session_state["pg_desc"] = desc_part.strip()
                            st.session_state["social_post"] = social_part.strip()
                        except Exception:
                            st.session_state["pg_headline"] = ""
                            st.session_state["pg_desc"] = result
                            st.session_state["social_post"] = result
                    else:
                        st.session_state["pg_headline"] = ""
                        st.session_state["pg_desc"] = result
                        st.session_state["social_post"] = result

    # --- DISPLAY RESULTS WITH COPY CONTAINERS ---
    if "pg_headline" in st.session_state:
        st.divider()
        st.markdown("### 🔴 PG Listing")
        
        # PropertyGuru Headline
        hl_len = len(st.session_state["pg_headline"])
        st.markdown(f"**1. PG Headline** `{hl_len} / 70 characters`")
        st.code(st.session_state["pg_headline"], language=None)
        
        # PropertyGuru Description
        desc_len = len(st.session_state["pg_desc"])
        st.markdown(f"**2. PG Description** `{desc_len} / 2000 characters`")
        st.code(st.session_state["pg_desc"], language=None)
        
        st.divider()
        st.markdown("### 🔵 Facebook & Instagram Post")
        st.markdown("**Copy-Paste Ready Post**")
        st.code(st.session_state["social_post"], language=None)
        
        st.caption("💡 *Tip: Hover over any box above and click the copy icon in the top right corner to instantly copy the text!*")

# --- TAB 2: VIDEO SHOT LIST ---
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

# --- TAB 3: PHOTO STAGING & VISION STUDIO ---
with tab3:
    st.subheader("AI Photo Declutter & Staging Vision")
    st.caption("Upload a photo of a room to let AI analyze its layout and generate precise staging / decluttering prompts.")
    
    uploaded_file = st.file_uploader("Upload Room Photo (JPG or PNG)", type=["jpg", "jpeg", "png"])
    
    col_img, col_opts = st.columns([1, 1])
    
    with col_img:
        if uploaded_file is not None:
            uploaded_image = Image.open(uploaded_file)
            st.image(uploaded_image, caption="Uploaded Room Photo", use_container_width=True)
        else:
            uploaded_image = None
            st.info("Please upload a photo above to unlock Vision features.")

    with col_opts:
        staging_goal = st.selectbox(
            "Select Staging Goal:",
            [
                "Virtual Declutter & Clean (Remove clutter/furniture)",
                "Virtual Staging: Modern Scandinavian",
                "Virtual Staging: Luxury Minimalist",
                "Virtual Staging: Contemporary Warm",
                "Enhance Lighting & Window View"
            ]
        )
        custom_notes = st.text_area(
            "Custom Edits / Retain Details (Optional):",
            placeholder="e.g., Keep original parquet flooring, replace dark sofa with beige leather sofa, add modern art on back wall."
        )

    if st.button("Analyze Photo & Generate AI Prompt", type="primary"):
        if uploaded_image is None:
            st.error("Please upload an image first!")
        else:
            prompt = f"""
            Analyze this uploaded room photograph in detail as a real estate photo editing expert.
            
            Target Editing Goal: {staging_goal}
            Custom User Instructions: {custom_notes if custom_notes else 'None'}
            
            Perform the following:
            1. Briefly describe the room's key architectural elements visible in the photo (flooring, lighting, window positions, room layout).
            2. Generate a highly detailed, technical AI Inpainting/Generation Prompt (optimized for Photoshop Generative Fill, Midjourney, or Photoshop) to achieve the target editing goal while preserving original room geometry and flooring.
            3. Provide step-by-step instructions on what area to select/mask in photo editing tools.
            """
            
            with st.spinner("AI Vision is analyzing your photograph..."):
                result = generate_real_estate_content(prompt, ai_engine, image=uploaded_image)
                if result:
                    st.success("Analysis & Staging Prompt Ready!")
                    st.markdown(result)
