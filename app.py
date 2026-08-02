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

tab1, tab2, tab3, tab4 = st.tabs([
    "✍️ Listing Copywriter", 
    "🎬 Video Shot List", 
    "🖼️ Photo Staging Studio",
    "📐 Floor Plan Studio"
])

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
    st.subheader("🖼️ AI Photo Declutter & Staging Vision")
    st.caption("Upload a room photo to generate optimized prompts for ChatGPT or Nano Banana image editing.")
    
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
            "Select Staging / Editing Goal:",
            [
                "Light Declutter (Remove loose items, keep main furniture intact)",
                "Full Reset (Empty room, keep structural items only)",
                "Virtual Staging: Modern Scandinavia",
                "Virtual Staging: Luxury Minimalist",
                "Virtual Staging: Contemporary Warm",
                "Virtual Staging: Japandi",
                "Virtual Staging: Wabi-Sabi",
                "Virtual Staging: Muji-Inspired"
            ]
        )
        custom_notes = st.text_area(
            "Custom Details / Notes (Optional):",
            placeholder="e.g., Preserve original parquet flooring, replace dark sofa with cream linen couch, keep unblocked balcony view..."
        )

    if st.button("Analyze Photo & Generate Prompt", type="primary"):
        if uploaded_image is None:
            st.error("Please upload an image first!")
        else:
            prompt = f"""
            Act as an expert real estate photo staging technician and AI prompt engineer.
            Analyze the uploaded photograph and write an optimized image-editing prompt for ChatGPT or Nano Banana (Google Image AI).

            Target Staging Goal: {staging_goal}
            Custom Instructions: {custom_notes if custom_notes else 'None'}

            Perform the following 2 tasks strictly:

            1. Architectural Analysis:
               - Briefly analyze and describe the key architectural and structural elements in the photo (room layout, ceiling height, window and door placements, lighting direction, flooring material/color, wall colors).

            2. ChatGPT / Nano Banana Copy-Paste Prompt:
               - Write a precise, highly detailed image-to-image text prompt designed to be pasted directly into ChatGPT or Nano Banana alongside this photo.
               - Mandatory Preservation Rules: Preservation clause MUST be explicit. Do NOT alter original room geometry, wall positions, window/door placements, ceiling height, structural colors, or flooring materials.
               - Mandatory Staging Rules depending on goal:
                 * If 'Light Declutter': Instruct the AI to detect and remove loose surface clutter (toys, boxes, cups, papers, trash, cables) from floors, tables, and cabinets, while keeping all main furniture (sofas, tables, built-in cabinets, bed frames, rugs) intact.
                 * If 'Full Reset Declutter': Instruct the AI to remove all movable furniture, decor, and clutter completely, resetting the room to a pristine empty state while preserving all original walls, doors, windows, ceiling, and flooring intact.
                 * If 'Virtual Staging' (Japandi / Wabi-Sabi / Muji-Inspired / etc.): Specify authentic interior materials, color palettes, organic wood, linen textures, muted earthy tones, paper or ceramic accents, proper scale, natural light direction matching, soft contact shadows under placed furniture, and high-end real estate photography finish.
               - High-End Real Estate Photography Enhancement: Ensure the prompt requests bright, professional, crisp exposure, clear window views, balanced daylighting, realistic contact shadows, and high-resolution architectural photo quality without distorting physical room boundaries.

            Format the final response with the following exact markers:
            ---ARCHITECTURAL_ANALYSIS---
            [Insert Architectural Analysis here]

            ---STAGING_PROMPT---
            [Insert the exact, copy-paste ready text prompt for ChatGPT or Nano Banana here. Clean text, no markdown bolding inside the prompt string itself.]
            """

            with st.spinner("AI Vision is analyzing your photograph..."):
                result = generate_real_estate_content(prompt, ai_engine, image=uploaded_image)
                
                if result:
                    if "---ARCHITECTURAL_ANALYSIS---" in result and "---STAGING_PROMPT---" in result:
                        try:
                            parts = result.split("---ARCHITECTURAL_ANALYSIS---")[1]
                            analysis_part, prompt_part = parts.split("---STAGING_PROMPT---")
                            st.session_state["staging_analysis"] = analysis_part.strip()
                            st.session_state["staging_prompt"] = prompt_part.strip()
                        except Exception:
                            st.session_state["staging_analysis"] = "Room Analysis complete."
                            st.session_state["staging_prompt"] = result
                    else:
                        st.session_state["staging_analysis"] = "Room Analysis complete."
                        st.session_state["staging_prompt"] = result

    # --- DISPLAY RESULTS WITH COPY CONTAINER ---
    if "staging_prompt" in st.session_state:
        st.divider()
        st.markdown("### 🏛️ Room Architectural Analysis")
        st.markdown(st.session_state.get("staging_analysis", ""))
        
        st.divider()
        st.markdown("### 📋 Copy-Paste Prompt for ChatGPT / Nano Banana")
        st.caption("Copy this prompt directly into ChatGPT or Nano Banana alongside your uploaded photo.")
        st.code(st.session_state["staging_prompt"], language=None)
        
        st.caption("💡 *Tip: Click the copy icon in the top right corner of the box above to instantly copy your prompt!*")

# --- TAB 4: 2D TO 3D FLOOR PLAN STUDIO ---
with tab4:
    st.header("📐 2D to 3D Floor Plan Studio")
    st.write(
        "Upload a 2D floor plan image to decode architectural symbols (walls, doors, windows), "
        "analyze spatial flow, and generate a photorealistic 3D rendering prompt with raised walls and custom interior styling."
    )

    # File uploader for 2D Floor Plan
    uploaded_plan = st.file_uploader(
        "Upload 2D Floor Plan (JPG, PNG)", 
        type=["jpg", "jpeg", "png"], 
        key="fp_3d_uploader"
    )

    if uploaded_plan is not None:
        col_img, col_settings = st.columns([1, 1])

        with col_img:
            st.image(uploaded_plan, caption="Uploaded 2D Floor Plan", use_container_width=True)

        with col_settings:
            st.subheader("⚙️ 3D Render Controls")
            
            design_style = st.selectbox(
                "Interior Design Style",
                [
                    "Japandi Minimalism (Warm Light Wood, Neutral Tones, Organic Elements)",
                    "Wabi-Sabi Warmth (Textured Plaster, Earthy Palette, Curved Furniture)",
                    "Modern Scandinavian (Light Oak, Crisp White Walls, Cozy Accents)",
                    "Luxury Modern (Slab Marble, Brass Accents, Plush Charcoal Upholstery)",
                    "Muji-Inspired (Clean Functional Layout, Soft Linen Fabrics, Light Timber)",
                    "Contemporary Urban Minimalist (Sleek Mattes, Glass Panels, Recessed LEDs)",
                    "Warm Industrial Loft (Exposed Concrete Accents, Black Metal Trim, Brick)"
                ]
            )

            camera_view = st.selectbox(
                "3D Camera Viewpoint",
                [
                    "45° Isometric 3D Cutaway (Best for overall spatial layout & wall height)",
                    "Overhead Top-Down 3D Floor Plan View",
                    "Eye-Level Architectural Walkthrough View",
                    "Axonometric Maquette Model on Clean Studio Background"
                ]
            )

            flooring_type = st.selectbox(
                "Flooring Material",
                [
                    "Light Oak Timber Flooring",
                    "Large-Format Off-White Marble Tiles",
                    "Light Beige Seamless Vinyl Planks",
                    "Herringbone Hardwood Parquet",
                    "Polished Light Microcement"
                ]
            )

            wall_finish = st.selectbox(
                "Wall & Trim Finishes",
                [
                    "Warm Cream/Beige Plaster with Matte White Trim",
                    "Crisp Architectural White Walls",
                    "Light Textured Lime-wash Plaster",
                    "Soft Grey Accent Walls & Off-White Trim"
                ]
            )

            lighting_style = st.selectbox(
                "Lighting & Ambiance",
                [
                    "Soft Natural Daylight with Gentle Sunlight Shadows",
                    "Golden Hour Warm Daylight Streaming Through Windows",
                    "Bright Architectural Studio Lighting",
                    "Warm Evening Interior Recessed Ambient Lighting"
                ]
            )

            custom_notes = st.text_area(
                "Specific Furniture or Layout Instructions (Optional)",
                placeholder="E.g., Place L-shaped beige sofa against the living room wall, 6-seater oak dining table near kitchen entrance, king bed in master bedroom..."
            )

        st.markdown("---")
        
        if st.button("🚀 Analyze Floor Plan & Generate 3D Model Spec", type="primary", key="btn_gen_3d"):
            with st.spinner("Decoding architectural lines, wall boundaries, door swings, and crafting 3D render prompt..."):
                try:
                    from PIL import Image
                    img = Image.open(uploaded_plan)

                    prompt = f"""
You are an expert Architectural Visualizer, Spatial Planner, and AI Prompt Engineer.
Examine the uploaded 2D floor plan image in detail.

### STEP 1: ARCHITECTURAL SYMBOL DECODING
1. **Wall Structure:** Differentiate thick solid lines (load-bearing structural walls) from thinner interior partition walls.
2. **Openings:** Detect door swing arcs, glass sliding panel lines, and window locations.
3. **Room Inventory & Flow:** Identify all room labels (Living, Dining, Kitchen, Bedrooms, Bathrooms, Balcony, Yard, Utility) and trace key movement paths.

### STEP 2: 3D CONVERSION MASTER SPECIFICATION
Formulate a full architectural breakdown and a copy-pasteable 3D prompt for AI image generators (such as Nano Banana Pro, Midjourney v6/v8, ChatGPT Vision, or SDXL).

Apply these design preferences:
- **Style Theme:** {design_style}
- **Camera Perspective:** {camera_view}
- **Wall Height & Mode:** Raised 2.8m 3D walls shown in a cutaway section mode (no roof overhead so interior layout is fully visible).
- **Flooring Finish:** {flooring_type}
- **Wall Finishes:** {wall_finish}
- **Lighting Setup:** {lighting_style}
- **Custom Directives:** {custom_notes if custom_notes else "Furnish each room naturally according to its function and chosen style."}

---

### OUTPUT FORMAT:
Provide a clean response formatted with these exact markdown headers:

## 📐 1. Architectural Symbol & Layout Analysis
- **Structural Overview:** Analysis of load-bearing walls vs partition walls, door orientation, and window placement.
- **Room-by-Room Breakdown:** List each room's orientation, door access points, and spatial layout flow.

## 🎨 2. Master 3D Rendering Prompt (Copy-Paste Ready)
Provide a structured, raw prompt in a code box that can be directly pasted into Midjourney or Nano Banana Pro to render a photorealistic 3D cutaway model with raised walls, full interior furnishings, matching materials, and natural daylighting.
"""

                    # Send image + prompt to Gemini model
                    response = st.session_state.model.generate_content([prompt, img])

                    st.success("✅ 3D Floor Plan Analysis & Prompt Generated!")
                    st.markdown(response.text)

                except Exception as e:
                    st.error(f"Error analyzing 2D floor plan: {str(e)}")
