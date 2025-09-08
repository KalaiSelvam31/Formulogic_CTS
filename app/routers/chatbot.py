import os
import json
import google.generativeai as genai
from fastapi import APIRouter, HTTPException, status
from dotenv import load_dotenv
import requests

# Application-specific imports
from app import schemas

# --- Configuration ---
# Load environment variables from your .env file
load_dotenv()

# Configure the Google Generative AI client
try:
    # Ensure your GOOGLE_API_KEY is set in your .env file
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not found.")
    genai.configure(api_key=api_key)
except Exception as e:
    # This print statement helps debug startup issues
    print(f"CRITICAL: Failed to configure Google Generative AI. Error: {e}")

router = APIRouter()


CONVERSATION_STATE = {}

def get_drug_name_from_rxcui(rxcui: str) -> str | None:
    """
    Fetch the normalized drug name from an RxCUI using the RxNorm API.
    """
    url = f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/property.json?propName=RxNorm%20Name"
    response = requests.get(url)

    if response.status_code != 200:
        # This handles cases where the API call itself fails (e.g., server down)
        print(f"RxNorm API request failed with status {response.status_code}")
        return None

    data = response.json()
    # Navigate the JSON to find the drug name
    prop_concepts = data.get("propConceptGroup", {}).get("propConcept", [])
    if prop_concepts:
        return prop_concepts[0].get("propValue")
    return None

# --- Prompt Template ---
# This template defines the persona and strict response rules for the chatbot.
PBM_PROMPT = """
You are PBM OptiBot, a friendly website chatbot assistant for a Pharmacy Benefit Management (PBM) Optimization Platform.

🎯 Response Rules (strict):
- Act like a website chat widget.
- Keep answers short, crisp, and conversational.
- Use only 1–3 bullet points or 2–3 short lines.
- No paragraphs or long explanations.
- If unclear, ask one short clarifying question.

🧑‍🤝‍🧑 User Roles:
Patient | Doctor/Prescriber | Pharmacist | Insurer | PBM Administrator

💡 Topics:
Prescription costs • Copay savings • Therapeutic equivalence (FDA Orange Book, DrugBank) • Pharmacy availability • Utilization trends •
Formulary impact • PMPM/CPMM tracking • Cost savings • Dashboards & analytics • Feedback collection

📚 Knowledge Scope:
CMS Part D • FDA Orange Book • DrugBank
Focus: cost savings, formulary optimization, utilization prediction, CPMM tracking
Goal: cut pharmacy spend ~12% with ≥95% satisfaction

System context: {pbm_context}
"""

# --- Helper Functions ---

def load_pbm_context(role: str) -> dict:
    """
    Loads PBM context for a given role from pbm_context.json located in the project root.
    """
    # Path is relative to this file's location (app/routers/chatbot.py)
    file_path = os.path.join(os.path.dirname(__file__), "..", "..", "pbm_context.json")
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        # Return context for the specific role or a default message if not found
        return data.get(role, {"role": role, "note": f"No context found for '{role}'."})
    except FileNotFoundError:
        return {"error": "pbm_context.json not found in project root", "role": role}
    except Exception as e:
        return {"error": str(e), "role": role}

def format_response(text: str) -> str:
    """
    Ensures the AI's response is short, bulleted, and ends with a consistent closing phrase.
    """
    # Cleans and splits the response text into lines
    lines = [line.strip("•- ") for line in text.split("\n") if line.strip()]
    # Takes a maximum of 3 lines and formats them as bullets
    bullets = [f"• {line}" for line in lines[:3]]
    
    if not bullets:
        bullets = ["• I'm sorry, I couldn't find a clear answer."]
        
    bullets.append("→ Need more detail?")
    return "\n".join(bullets)

# --- API Route ---
@router.post("/chat", response_model=schemas.ChatResponse, tags=["Chatbot"])
def chat_with_bot(request: schemas.ChatRequest):
    """
    Handles chatbot interactions with special logic for RxCUI lookups.
    """
    session_id = request.session_id

    # --- Step 1: Check if we are waiting for an RxCUI from this session ---
    if CONVERSATION_STATE.get(session_id) == "waiting_for_rxcui":
        rxcui = request.message.strip()
        drug_name = get_drug_name_from_rxcui(rxcui)

        # Clean up the state regardless of the outcome
        del CONVERSATION_STATE[session_id]

        if drug_name:
            reply = f"Thank you! The medicine for RxCUI **{rxcui}** is **{drug_name}**. How else can I help?"
        else:
            reply = f"Sorry, I couldn't find a medicine for RxCUI `{rxcui}`. Please check the ID and we can try again."

        return schemas.ChatResponse(reply=reply)

    # --- Step 2: Check if the user's initial query is about a medicine ---
    medicine_keywords = ["medicine", "drug", "medication", "prescription"]
    if any(keyword in request.message.lower() for keyword in medicine_keywords):
        # Set the state to indicate we are now waiting for an RxCUI
        CONVERSATION_STATE[session_id] = "waiting_for_rxcui"
        reply = "I can help with that. What is the **RxCUI** of the medicine you're interested in?"
        return schemas.ChatResponse(reply=reply)

    # --- Step 3: If not a medicine query, use the general-purpose Generative AI ---
    context_data = load_pbm_context(request.role)
    prompt = PBM_PROMPT.format(pbm_context=context_data)

    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        response = model.generate_content([prompt, request.message])
        formatted_reply = format_response(response.text)
        return schemas.ChatResponse(reply=formatted_reply)
    except Exception as e:
        print(f"ERROR: Google Generative AI call failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The chatbot service is currently unavailable."
        )
