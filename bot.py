import os
import requests
import json
import base64
from google import genai

# Load Secret Keys from GitHub
GEMINI_KEY = os.environ["GEMINI_KEY"]
HF_TOKEN = os.environ["HF_TOKEN"]
# It will safely wait if the Pinterest token isn't added to secrets yet
PINTEREST_TOKEN = os.environ.get("PINTEREST_TOKEN", "WAITING") 
PINTEREST_BOARD_ID = "903112600217009679" 

# 1. Get the Hollywood Prompt from Gemini
print("Asking Gemini for a VFX concept...")
client = genai.Client(api_key=GEMINI_KEY)
prompt_logic = """
You are an elite VFX Art Director. Write a highly detailed, cinematic image prompt for an AI generator. 
The subject should be an epic nature landscape, a cinematic superhero, or historical architecture.
Use rendering terms like: Unreal Engine 5, OctaneRender, 85mm lens, volumetric lighting, photorealistic.
Return ONLY the raw prompt text, nothing else.
"""
response = client.models.generate_content(
    model='gemini-1.5-flash',
    contents=prompt_logic
)
vfx_prompt = response.text.strip()
print(f"Generated Prompt: {vfx_prompt}")

# 2. Generate the Image using Hugging Face (FLUX.1 Schnell)
print("Requesting image from Hugging Face...")
API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}
payload = {"inputs": vfx_prompt}

image_response = requests.post(API_URL, headers=headers, json=payload)

if image_response.status_code == 200:
    image_bytes = image_response.content
    print("Image generated successfully!")
else:
    print(f"Image generation failed: {image_response.text}")
    exit()

# 3. Upload to Pinterest
if PINTEREST_TOKEN != "WAITING":
    print("Uploading to Pinterest...")
    pinterest_url = "https://api.pinterest.com/v5/pins"
    pin_headers = {
        "Authorization": f"Bearer {PINTEREST_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    encoded_image = base64.b64encode(image_bytes).decode('utf-8')
    
    pin_payload = {
        "board_id": PINTEREST_BOARD_ID,
        "media_source": {
            "source_type": "image_base64",
            "content_type": "image/jpeg",
            "data": encoded_image
        },
        "title": "Cinematic Masterpiece",
        "description": f"{vfx_prompt} #cinematic #VFX #DigitalArt"
    }
    
    pin_response = requests.post(pinterest_url, headers=pin_headers, json=pin_payload)
    print(f"Pinterest Response: {pin_response.status_code}")
else:
    print("Bot ran successfully! Waiting on Pinterest token to enable uploading.")
