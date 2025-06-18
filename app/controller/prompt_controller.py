import os
import logging
import json
import uuid
from fastapi import Response, HTTPException, status
from dotenv import load_dotenv
from openai import OpenAI
from gtts import gTTS



logging.basicConfig(level=logging.INFO)

load_dotenv()

api_key = os.getenv("API_KEY")
backend_url = os.getenv('BACKEND_URL')

if not api_key:
    raise RuntimeError("Missing API_KEY in environment variables")


client = OpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

system_prompt = """
You are a helpful AI assistant whose name is Xonier Bot. You are an expert in breaking down complex problems and resolving queries. You are developed by Mridul, Your work is to help user about Xonier Technology
For any input, follow these steps strictly: "analyse", "think", "output", "validate", and finally "result". Xonier Technology founded by Dhirendra Kumar in 2019 and he is the also the position of  CEO of Xonier Technologies and Krishna Vasudevan is co-founder of xonier technologis. Xonier Technologies working on various Fields, Example: Block Chain, Artificial Intelligence, App Development, Software Development. Developing team Manager name is Ashraf Ali

Rules:
1. Follow strict JSON output as per output schema.
2. Always perform one step at a time and wait for the next input.
3. Carefully analyse the user query.

Output Format:
{step:"string",content:"string"}

Examples:
Input: What is 2+2
Output: {step:"analyse",content:"User gave me two numbers and wants to perform addition of these two and he is asking a basic maths question"}
Output: {step:"think",content:"To perform the addition I must go from left to right and add all the operands"}
Output: {step:"output",content:"4"}
Output: {step:"validate",content:"Seems like four is the correct answer for 2+2"}
Output: {step:"result",content:"2+2=4 and that is calculated by adding all numbers"}
"""


async def handle_incoming_prompt(response: Response, content: dict):
    prompt = content.get("content")
    if not prompt or not isinstance(prompt, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt must be a non-empty string."
        )

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        outputs = []

        while True:
            api_response = client.chat.completions.create(
                model='gemini-2.0-flash',
                response_format={"type": "json_object"},
                messages=messages
            )

            assistant_msg = api_response.choices[0].message.content
            messages.append({"role": "assistant", "content": assistant_msg})

            output = json.loads(assistant_msg)
            outputs.append(output.get("content"))

            if output.get("step") == "result":
                break
        result_msg = outputs[-1]
        tts = gTTS(text=result_msg, lang='en', slow=False )
        filename = f"speech_{uuid.uuid4()}.mp3"
        filepath = os.path.join("temp", filename)
      
       
        os.makedirs("temp", exist_ok=True)
        tts.save(filepath)
        
    
        response.status_code = status.HTTP_200_OK
        return {
            "message": "Response retrieved successfully",
            "step": result_msg,
            "audio_file": f"/audio/{filename}"
        }

    except Exception as e:
        logging.error(f"Error during Gemini request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gemini Error: {str(e)}"
        )