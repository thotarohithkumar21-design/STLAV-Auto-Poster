import os
import requests
import base64
import json
from google import genai
from google.genai import types

# Authentication Credentials
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID")
CF_API_TOKEN = os.environ.get("CF_API_TOKEN")
MAKE_WEBHOOK_URL = os.environ.get("MAKE_WEBHOOK_URL")

HISTORY_FILE = "history.txt"
IMAGE_FILE = "latest_image.jpg"

def get_previous_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return f.read().strip()
    return "No previous history."

def update_history(prompt_text):
    lines = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            lines = f.readlines()
    
    lines.append(f"{prompt_text}\n")
    if len(lines) > 15:
        lines = lines[-15:]
        
    with open(HISTORY_FILE, "w") as f:
        f.writelines(lines)

def generate_content(history):
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    system_instruction = """You are an elite concept artist and social media manager.
Your job is to generate a cinematic text-to-image prompt, and create a highly engaging Pinterest title, description, and hashtags.
Visual Requirements: Vertical composition, cinematic lighting, photorealistic 8k resolution.
Subject Matter Rotation: Select ONE of the following themes. NEVER repeat previous concepts.
1. Hindu Deities
2. Jesus
3. Islamic Visual Themes (Breathtaking architecture, glowing calligraphy)
4. Marvel Superheroes

Return a valid JSON object matching this schema exactly:
{
  "image_prompt": "The detailed cinematic prompt for the AI generator",
  "title": "A catchy Pinterest Title (max 100 chars)",
  "description": "An engaging description for the image.",
  "hashtags": "#epic #art #cinematic (3 to 5 relevant hashtags)"
}"""

    prompt_request = f"Previous concepts (AVOID THESE):\n{history}\n\nGenerate brand new JSON content."
    
    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=prompt_request,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.9,
            response_mime_type="application/json",
            tools=[]
        ),
    )
    return json.loads(response.text.strip())

def generate_image(prompt):
    clean_account_id = str(CF_ACCOUNT_ID).strip()
    url = f"https://api.cloudflare.com/client/v4/accounts/{clean_account_id}/ai/run/@cf/black-forest-labs/flux-1-schnell"
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt,
        "steps": 4
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        response.raise_for_status()
        
    data = response.json()
    b64_image = data['result']['image']
    
    # Save a copy locally to repo
    with open(IMAGE_FILE, "wb") as f:
        f.write(base64.b64decode(b64_image))
        
    return b64_image

def post_to_make(metadata, b64_image):
    print("Sending clean JSON data to Make.com...")
    full_description = f"{metadata['description']}\n\n{metadata['hashtags']}"
    
    payload = {
        "title": metadata["title"],
        "description": full_description,
        "image_base64": b64_image
    }
    
    response = requests.post(MAKE_WEBHOOK_URL, json=payload)
    if response.status_code == 200:
        print("Successfully sent to Make.com!")
    else:
        print(f"Webhook Error: {response.text}")

def main():
    print("Reading memory log...")
    history = get_previous_history()
    
    print("Generating new concept and Pinterest metadata...")
    metadata = generate_content(history)
    print(f"Generated Title: {metadata['title']}")
    
    print("Rendering image via Cloudflare...")
    b64_image = generate_image(metadata["image_prompt"])
    
    post_to_make(metadata, b64_image)
    
    print("Updating memory log...")
    update_history(metadata["image_prompt"])
    print("Execution complete.")

if __name__ == "__main__":
    main()
