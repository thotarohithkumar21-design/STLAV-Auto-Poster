import os
import requests
import base64
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

def update_history(prompt):
    lines = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            lines = f.readlines()
    
    lines.append(f"{prompt}\n")
    if len(lines) > 15:
        lines = lines[-15:]
        
    with open(HISTORY_FILE, "w") as f:
        f.writelines(lines)

def generate_prompt(history):
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    system_instruction = """You are an elite concept artist and blockbuster film cinematographer. Your job is to write highly detailed, evocative text-to-image prompts for a state-of-the-art image generator.
Core Objective: Generate a single, highly descriptive paragraph that paints a vivid, story-driven scene in vertical portrait orientation. The image must look like a high-budget cinematic masterpiece.
Visual Requirements:
- Framing: Vertical composition, portrait orientation.
- Lighting: Always specify high-end lighting techniques (e.g., volumetric rays, chiaroscuro).
- Camera & Composition: Include precise lens details and angles.
- Quality: Enforce maximum visual fidelity (e.g., 8k resolution, photorealistic).

Subject Matter Rotation: Select ONE of the following themes. CRUCIAL: Never generate the same scenario twice. Review the history and ensure this prompt is entirely different.
1. Hindu Deities
2. Jesus
3. Islamic Visual Themes (Breathtaking architecture, glowing calligraphy)
4. Marvel Superheroes

Output Format: Return ONLY the final image prompt text. Do not include quotes, pleasantries, or formatting."""

    prompt_request = f"Previous generated prompts (AVOID REPEATING THESE):\n{history}\n\nGenerate a brand new, completely unique prompt following the system instructions."
    
    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=prompt_request,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.9,
            tools=[]
        ),
    )
    return response.text.strip()

def generate_image(prompt):
    clean_account_id = str(CF_ACCOUNT_ID).strip()
    url = f"https://api.cloudflare.com/client/v4/accounts/{clean_account_id}/ai/run/@cf/black-forest-labs/flux-1-schnell"
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt,
        "steps": 4,
        "width": 576,
        "height": 1024
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        response.raise_for_status()
        
    data = response.json()
    image_bytes = base64.b64decode(data['result']['image'])
    
    with open(IMAGE_FILE, "wb") as f:
        f.write(image_bytes)

def post_to_pinterest(prompt):
    print("Sending image to Make.com webhook...")
    with open(IMAGE_FILE, "rb") as f:
        # We attach the image file and the prompt text
        files = {'file': (IMAGE_FILE, f, 'image/jpeg')}
        data = {'description': prompt}
        response = requests.post(MAKE_WEBHOOK_URL, files=files, data=data)
    
    if response.status_code == 200:
        print("Successfully routed to Make.com!")
    else:
        print(f"Webhook Error: {response.text}")

def main():
    history = get_previous_history()
    new_prompt = generate_prompt(history)
    print(f"Generated Prompt:\n{new_prompt}\n")
    generate_image(new_prompt)
    post_to_pinterest(new_prompt)
    update_history(new_prompt)
    print("Execution complete.")

if __name__ == "__main__":
    main()
