import os
import requests
import base64
from google import genai
from google.genai import types

# Authentication Credentials
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID")
CF_API_TOKEN = os.environ.get("CF_API_TOKEN")

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
    # Keep only the last 15 entries to maintain context limit
    if len(lines) > 15:
        lines = lines[-15:]
        
    with open(HISTORY_FILE, "w") as f:
        f.writelines(lines)

def generate_prompt(history):
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    system_instruction = """You are an elite concept artist and blockbuster film cinematographer. Your job is to write highly detailed, evocative text-to-image prompts for a state-of-the-art image generator.
Core Objective: Generate a single, highly descriptive paragraph that paints a vivid, story-driven scene. The image must look like a high-budget cinematic masterpiece.
Visual Requirements:
- Lighting: Always specify high-end lighting techniques (e.g., volumetric rays, chiaroscuro, dramatic rim lighting).
- Camera & Composition: Include precise lens details and angles (e.g., 35mm anamorphic, low-angle).
- Quality: Enforce maximum visual fidelity (e.g., 8k resolution, photorealistic, highly detailed).

Subject Matter Rotation: Select ONE of the following themes. CRUCIAL: Never generate the same scenario twice. Review the history and ensure this prompt is entirely different.
1. Hindu Deities
2. Jesus
3. Islamic Visual Themes (Breathtaking architecture, glowing calligraphy)
4. Marvel Superheroes

Output Format: Return ONLY the final image prompt text. Do not include quotes, pleasantries, or formatting."""

    prompt_request = f"Previous generated prompts (AVOID REPEATING THESE):\n{history}\n\nGenerate a brand new, completely unique prompt following the system instructions."
    
    # FIX: Updated config structure to prevent the AFC warning crash
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt_request,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.9,
            tools=[] # Explicitly pass an empty list to bypass the AFC bug
        ),
    )
    return response.text.strip()

def generate_image(prompt):
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt,
        "steps": 4
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    
    b64_image = data['result']['image']
    image_bytes = base64.b64decode(b64_image)
    
    with open(IMAGE_FILE, "wb") as f:
        f.write(image_bytes)

def main():
    print("Reading memory log...")
    history = get_previous_history()
    
    print("Generating new cinematic concept...")
    new_prompt = generate_prompt(history)
    print(f"Generated Prompt:\n{new_prompt}\n")
    
    print("Rendering image via Cloudflare...")
    generate_image(new_prompt)
    
    print("Updating memory log...")
    update_history(new_prompt)
    
    print("Execution complete. Image successfully saved.")

if __name__ == "__main__":
    main()
