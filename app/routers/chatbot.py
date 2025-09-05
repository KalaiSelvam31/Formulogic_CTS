import os
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv
import google.generativeai as genai
from app.schemas import ChatRequest, ChatResponse

load_dotenv()

router = APIRouter()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY environment variable not set.")

genai.configure(api_key=GOOGLE_API_KEY)

chat_histories = {}

@router.post("/chat", response_model=ChatResponse)
async def chat_with_bot(request: ChatRequest):

    try:

        model = genai.GenerativeModel('gemini-1.5-flash-latest')

        if request.session_id not in chat_histories:
            chat_histories[request.session_id] = model.start_chat(history=[])

        chat_session = chat_histories[request.session_id]

        response = chat_session.send_message(request.message)

        return ChatResponse(reply=response.text)

    except Exception as e:

        print(f"An error occurred: {e}")
     
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")

