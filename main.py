import os
import json
import random
import asyncio
import requests
import edge_tts
from google import genai
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 1. Generate 100% English GTA 6 Short Script using Gemini
def generate_gta6_script():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
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
        "search_keywords": ["neon city", "sports car", "miami beach", "gaming"]
    }}
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    raw_text = response.text.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(raw_text)

# 2. Create Natural English Male Voiceover
async def create_voiceover(text, output_audio="voice.mp3"):
    communicate = edge_tts.Communicate(text, voice="en-US-ChristopherNeural", rate="+8%")
    await communicate.save(output_audio)

# 3. Fetch Background Video Clips from Pixabay
def download_clips(keywords):
    api_key = os.environ["PIXABAY_API_KEY"]
    clip_files = []
    for idx, kw in enumerate(keywords[:4]):
        query = requests.utils.quote(kw)
        url = f"https://pixabay.com{api_key}&q={query}&per_page=5"
        res = requests.get(url).json()
        hits = res.get("hits", [])
        if not hits:
            fallback_url = f"https://pixabay.com{api_key}&q=neon+city&per_page=5"
            hits = requests.get(fallback_url).json().get("hits", [])
        if hits:
            video_choice = random.choice(hits)
            video_url = video_choice["videos"]["medium"]["url"]
            filename = f"clip_{idx}.mp4"
            with open(filename, "wb") as f:
                f.write(requests.get(video_url).content)
            clip_files.append(filename)
    return clip_files

# 4. Crop and Assemble Final 1080x1920 Vertical YouTube Short
def build_video(clip_files, audio_file="voice.mp3", output_video="gta6_short.mp4"):
    audio = AudioFileClip(audio_file)
    duration = audio.duration
    sub_duration = duration / len(clip_files)
    processed_clips = []

    for path in clip_files:
        clip = VideoFileClip(path).without_audio()
        if clip.duration < sub_duration:
            clip = clip.loop(duration=sub_duration)
        else:
            clip = clip.subclip(0, sub_duration)
        
        # Resize and center-crop to 9:16 vertical (1080x1920)
        clip = clip.resize(height=1920)
        if clip.w < 1080:
            clip = clip.resize(width=1080)
        clip = clip.crop(x_center=clip.w / 2, y_center=clip.h / 2, width=1080, height=1920)
        processed_clips.append(clip)

    final_video = concatenate_videoclips(processed_clips, method="compose").set_audio(audio)
    final_video.write_videofile(output_video, fps=30, codec="libx264", audio_codec="aac")

# 5. Upload to Your New GTA 6 YouTube Channel
def upload_to_youtube(video_path, title, description):
    creds = Credentials(
        token=None,
        refresh_token=os.environ["REFRESH_TOKEN"],
        token_uri="https://googleapis.com",
        client_id=os.environ["CLIENT_ID"],
        client_secret=os.environ["CLIENT_SECRET"],
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
    clips = download_clips(data["search_keywords"])
    build_video(clips)
    upload_to_youtube("gta6_short.mp4", data["title"], data["description"])
