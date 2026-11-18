import os
import json
import time
import random
import asyncio
import requests
import edge_tts
from PIL import Image
from io import BytesIO
from google import genai
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 1. Generate 100% English GTA 6 Short Script
def generate_gta6_script():
    api_key = os.environ["GEMINI_API_KEY"].strip()
    client = genai.Client(api_key=api_key)
    topics = [
        "Vice City map secrets and Leonida locations in GTA 6",
        "Lucia and Jason character backstory and gameplay mechanics in GTA 6",
        "craziest realistic graphics and AI details in Grand Theft Auto 6",
        "weapons, cars, and heists coming to GTA 6",
        "hidden Easter eggs in the GTA 6 trailer you missed"
    ]
    chosen_topic = random.choice(topics)
    prompt = f"""
    Create a fast-paced, exciting 40-second YouTube Short script in English about: {chosen_topic}.
    Return ONLY valid JSON with these exact keys:
    {{
        "title": "Catchy English title under 60 characters #GTA6 #Shorts",
        "description": "Engaging English description with hashtags #GTA6 #GrandTheftAuto6 #Gaming #Shorts",
        "narration": "Engaging 75-word English voiceover script without stage directions or emojis.",
        "search_keywords": ["Miami skyline night", "sports car neon", "Miami beach sunset", "video game controller"]
    }}
    """
    models_to_try = ["gemini-3.5-flash-lite", "gemini-3.0-flash", "gemini-2.5-flash"]
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            raw_text = response.text.strip().replace("```json", "").replace("```", "").strip()
            return json.loads(raw_text)
        except Exception as e:
            print(f"Model {model_name} busy, trying next... Error: {e}")
            time.sleep(5)
    raise RuntimeError("All Gemini models are temporarily busy.")

# 2. Create Natural English Male Voiceover
async def create_voiceover(text, output_audio="voice.mp3"):
    communicate = edge_tts.Communicate(text, voice="en-US-ChristopherNeural", rate="+8%")
    await communicate.save(output_audio)

# 3. Fetch High-Res Visuals from Wikimedia Commons (100% Free, No API Key Needed!)
def download_visuals(keywords):
    headers = {"User-Agent": "GTA6ShortsBot/1.0 (https://github.com)"}
    image_files = []
    search_list = (keywords[:5] if keywords else []) + ["Miami night", "Lamborghini", "Miami Beach", "Neon city", "Police car"]

    for kw in search_list:
        if len(image_files) >= 5:
            break
        url = "https://wikimedia.org"
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": f"filetype:bitmap {kw}",
            "gsrnamespace": 6,
            "gsrlimit": 5,
            "prop": "imageinfo",
            "iiprop": "url|size"
        }
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15).json()
            pages = resp.get("query", {}).get("pages", {})
            for page in pages.values():
                info = page.get("imageinfo", [{}])
                img_url = info.get("url", "")
                if img_url.lower().endswith((".jpg", ".jpeg", ".png")) and info.get("width", 0) >= 800:
                    img_data = requests.get(img_url, headers=headers, timeout=15).content
                    img = Image.open(BytesIO(img_data)).convert("RGB")
                    
                    # Resize and center-crop to 1080x1920 (9:16 vertical)
                    target_w, target_h = 1080, 1920
                    scale = max(target_w / img.width, target_h / img.height)
                    new_size = (int(img.width * scale), int(img.height * scale))
                    img = img.resize(new_size, Image.LANCZOS)
                    left = (img.width - target_w) // 2
                    top = (img.height - target_h) // 2
                    img = img.crop((left, top, left + target_w, top + target_h))
                    
                    filename = f"scene_{len(image_files)}.jpg"
                    img.save(filename, quality=95)
                    image_files.append(filename)
                    break
        except Exception as e:
            print(f"Skipping {kw}: {e}")

    if not image_files:
        raise ValueError("Could not fetch images from Wikimedia.")
    return image_files

# 4. Create Dynamic Zooming 1080x1920 YouTube Short
def build_video(image_files, audio_file="voice.mp3", output_video="gta6_short.mp4"):
    audio = AudioFileClip(audio_file)
    duration = audio.duration
    sub_duration = duration / len(image_files)
    clips = []

    for idx, img_path in enumerate(image_files):
        clip = ImageClip(img_path).set_duration(sub_duration)
        # Smooth Ken Burns zoom-in effect so the Short feels dynamic
        clip = clip.resize(lambda t: 1.0 + 0.08 * (t / sub_duration))
        clip = clip.set_position(("center", "center"))
        clips.append(clip)

    final_video = concatenate_videoclips(clips, method="compose").set_audio(audio)
    final_video.write_videofile(output_video, fps=30, codec="libx264", audio_codec="aac")

# 5. Upload to Your New GTA 6 YouTube Channel
def upload_to_youtube(video_path, title, description):
    creds = Credentials(
        token=None,
        refresh_token=os.environ["REFRESH_TOKEN"].strip(),
        token_uri="https://googleapis.com",
        client_id=os.environ["CLIENT_ID"].strip(),
        client_secret=os.environ["CLIENT_SECRET"].strip(),
    )
    youtube = build("youtube", "v3", credentials=creds)
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["GTA 6", "Grand Theft Auto 6", "GTA VI", "Gaming Shorts", "Rockstar Games"],
            "categoryId": "20"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    print("SUCCESS! Uploaded GTA 6 Short. Video ID:", response["id"])

if __name__ == "__main__":
    data = generate_gta6_script()
    asyncio.run(create_voiceover(data["narration"]))
    visuals = download_visuals(data["search_keywords"])
    build_video(visuals)
    upload_to_youtube("gta6_short.mp4", data["title"], data["description"])
