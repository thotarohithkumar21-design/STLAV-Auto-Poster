import os
import requests
import json
import base64
from google import genai
from google.genai import types
import random

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
  "image_prompt": "The detailed cinematic prompt",
  "title": "A catchy Pinterest Title (max 100 chars)",
  "description": "An engaging description.",
  "hashtags": "#epic #art (3 to 5 relevant hashtags)"
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
    payload = {"prompt": prompt, "steps": 4}
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    b64_image = data['result']['image']
    with open(IMAGE_FILE, "wb") as f:
        f.write(base64.b64decode(b64_image))

def push_to_github():
    print("Pushing image directly to GitHub servers...")
    # This automatically uploads the image to your repository before Make.com triggers
    os.system('git config --global user.name "AI-Art-Director"')
    os.system('git config --global user.email "actions@github.com"')
    os.system('git add history.txt latest_image.jpg')
    os.system('git commit -m "Auto-generated image prior to webhook" || echo "No changes"')
    os.system('git push')

def post_to_make(metadata):
    # A random number is added so Pinterest always grabs the freshest image, ignoring caches
    cache_buster = random.randint(100000, 999999)
    github_image_url = f"https://raw.githubusercontent.com/thotarohithkumar21-design/STLAV-Auto-Poster/main/latest_image.jpg?v={cache_buster}"
    
    print(f"Sending GitHub URL to Make.com: {github_image_url}")
    full_description = f"{metadata['description']}\n\n{metadata['hashtags']}"
    payload = {
        "title": metadata["title"],
        "description": full_description,
        "image_url": github_image_url
    }
    requests.post(MAKE_WEBHOOK_URL, json=payload)

def main():
    history = get_previous_history()
    metadata = generate_content(history)
    generate_image(metadata["image_prompt"])
    update_history(metadata["image_prompt"])
    
    # 1. Push to GitHub first
    push_to_github()
    
    # 2. Send the live link to Make.com second
    post_to_make(metadata)
    
    print("Execution complete.")

if __name__ == "__main__":
    main()
