import os
import json
import time
import random
import asyncio
import edge_tts
from PIL import Image, ImageDraw
from io import BytesIO
from google import genai
from google.genai import types
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 1. Generate 100% English GTA 6 Short Script & AI Image Prompts
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
        "image_prompts": [
            "Vice City neon skyline at sunset, palm trees, sports cars, GTA 6 art style, vertical 9:16",
            "Futuristic supercar drifting on a neon Miami highway at night, GTA 6 aesthetic, vertical 9:16",
            "Two action game characters overlooking a tropical beachfront city at dusk, cinematic lighting, vertical 9:16",
            "High speed police chase on a coastal bridge at night with neon lights, video game art, vertical 9:16"
        ]
    }}
    """
    models_to_try = ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-3.5-flash-lite"]
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

# 3. Generate Custom 9:16 GTA 6 Style AI Images via Gemini Flash Image
def generate_visuals(image_prompts):
    api_key = os.environ["GEMINI_API_KEY"].strip()
    client = genai.Client(api_key=api_key)
    image_files = []

    for idx, img_prompt in enumerate(image_prompts[:4]):
        filename = f"scene_{idx}.jpg"
        saved = False
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=f"Generate a vibrant 9:16 vertical gaming illustration: {img_prompt}",
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio="9:16")
                )
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    img = Image.open(BytesIO(part.inline_data.data)).convert("RGB")
                    img = img.resize((1080, 1920), Image.LANCZOS)
                    img.save(filename, quality=95)
                    image_files.append(filename)
                    saved = True
                    print(f"Generated AI image {idx+1}/4 successfully!")
                    break
        except Exception as e:
            print(f"Image generation fallback for scene {idx}: {e}")

        if not saved:
            # Sleek Vice City Neon Gradient Fallback (Fixed tuple indexing)
            img = Image.new("RGB", (1080, 1920), (15, 10, 35))
            draw = ImageDraw.Draw(img)
            colors = [(255, 45, 149), (0, 229, 255), (140, 45, 255), (255, 140, 0)]
            c = colors[idx % len(colors)]
            for y in range(1920):
                ratio = y / 1920.0
                r = int(15 + (c[0] * ratio) * 0.6)
                g = int(10 + (c[1] * ratio) * 0.6)
                b = int(35 + (c[2] * ratio) * 0.6)
                draw.line([(0, y), (1080, y)], fill=(r, g, b))
            img.save(filename, quality=95)
            image_files.append(filename)

    return image_files

# 4. Create Dynamic Zooming 1080x1920 YouTube Short
def build_video(image_files, audio_file="voice.mp3", output_video="gta6_short.mp4"):
    audio = AudioFileClip(audio_file)
    duration = audio.duration
    sub_duration = duration / len(image_files)
    clips = []

    for img_path in image_files:
        clip = ImageClip(img_path).set_duration(sub_duration)
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
        token_uri="https://oauth2.googleapis.com/token",
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
    visuals = generate_visuals(data["image_prompts"])
    build_video(visuals)
    upload_to_youtube("gta6_short.mp4", data["title"], data["description"])
