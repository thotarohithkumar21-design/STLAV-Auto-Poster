import os
import requests
import json
from google import genai
from google.genai import types

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID")
CF_API_TOKEN = os.environ.get("CF_API_TOKEN")
MAKE_WEBHOOK_URL = os.environ.get("MAKE_WEBHOOK_URL")
HISTORY_FILE = "history.txt"
IMAGE_FILE = "latest_image.jpg"

def main():
    # 1. Generate Metadata
    client = genai.Client(api_key=GEMINI_API_KEY)
    resp = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=f"History:\n{open(HISTORY_FILE).read() if os.path.exists(HISTORY_FILE) else ''}\nGenerate a vertical cinematic prompt, title, desc, and hashtags for a Hindu Deity, Jesus, Islamic Art, or Marvel. Do not repeat history.",
        config=types.GenerateContentConfig(
            system_instruction='Return exact JSON: {"image_prompt": "...", "title": "...", "description": "...", "hashtags": "..."}',
            response_mime_type="application/json", temperature=0.9, tools=[]
        )
    )
    meta = json.loads(resp.text.strip())
    
    # 2. Generate Image
    url = f"https://api.cloudflare.com/client/v4/accounts/{str(CF_ACCOUNT_ID).strip()}/ai/run/@cf/black-forest-labs/flux-1-schnell"
    img_resp = requests.post(url, headers={"Authorization": f"Bearer {CF_API_TOKEN}"}, json={"prompt": meta["image_prompt"], "steps": 4})
    img_resp.raise_for_status()
    with open(IMAGE_FILE, "wb") as f:
        import base64
        f.write(base64.b64decode(img_resp.json()['result']['image']))

    # 3. Upload for public URL
    print("Uploading to get public URL...")
    with open(IMAGE_FILE, 'rb') as f:
        url_resp = requests.post('https://catbox.moe/user/api.php', data={'reqtype': 'fileupload'}, files={'fileToUpload': f})
    public_url = url_resp.text.strip()

    # 4. Send to Make.com
    print(f"Sending URL to Make.com: {public_url}")
    requests.post(MAKE_WEBHOOK_URL, json={
        "title": meta["title"],
        "description": f"{meta['description']}\n\n{meta['hashtags']}",
        "image_url": public_url
    })
    
    # 5. Update Memory
    with open(HISTORY_FILE, "a") as f: f.write(meta["image_prompt"] + "\n")
    print("Execution complete.")

if __name__ == "__main__":
    main()
