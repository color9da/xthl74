import os, json, glob, requests, shutil, sys, time, random
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

try:
    from upload.upload_youtube import upload_to_youtube
except ImportError as e:
    print(f"Import error: {e}")
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return []
    return []

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({"video_name": video_name, "metadata": metadata})
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))
    if specific_video:
        if os.path.exists(specific_video):
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video
        if os.path.exists(vid_path):
            if name in published:
                print(f"Reposting video: {name}")
            return vid_path, name
        print(f"Video not found: {name}")
        return None, None
    for vid in all_videos:
        name = os.path.basename(vid)
        if name not in published:
            return vid, name
    return None, None

def generate_caption():
    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")
    if not api_key:
        print("No POLLINATIONS_API_KEY. Using default.")
        return "Stunning walk!", "A walk to remember..."
    vibes = ["sassy and confident", "mysterious and elegant", "playful and cheeky", "high-fashion boss", "romantic and dreamy"]
    chosen_vibe = random.choice(vibes)
    prompt = (
        f"Write a completely unique, funny, and engaging title and description for a YouTube Short "
        f"of me, Luzara Voss. In the video, I am a beautiful model walking away from the "
        f"camera and looking back. Speak in the first person. Make the vibe {chosen_vibe}. "
        f"Make it interaction-bait to gain followers. "
        f"Include relevant hashtags in ALL LOWERCASE like #vibes #catwalkmodel #model #walking. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )
    try:
        resp = requests.post("https://gen.pollinations.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.9, "seed": random.randint(1, 999999)}, timeout=30)
        content = resp.json()['choices'][0]['message']['content']
        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)
        return result.get("title", "Stunning walk!"), result.get("description", "A beautiful walk...")
    except Exception as e:
        print(f"Caption error: {e}")
        return "Stunning walk!", "A beautiful walk... #fashion #model"

def main():
    print("=" * 60)
    print("YOUTUBE SHORTS UPLOAD STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("No video to publish")
        return
    
    print(f"Video: {video_name}")
    print("Generating caption...")
    title, description = generate_caption()
    print(f"Title: {title}")
    
    youtube_ok = False
    try:
        upload_to_youtube(video_path, title, description, tags=["fashion", "model", "walking", "shorts"])
        youtube_ok = True
    except Exception as e:
        print(f"YouTube upload failed: {e}")
    
    mark_as_published(video_name, {"title": title, "description": description, "youtube": youtube_ok})
    
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
    video_in_processed = os.path.join(PROCESSED_DIR, video_name)
    is_repost = os.path.exists(video_in_processed) and os.path.samefile(video_path, video_in_processed)
    if not is_repost:
        try:
            shutil.move(video_path, os.path.join(published_dir, video_name))
        except Exception as e:
            print(f"Move failed: {e}")
    
    print("DONE")

if __name__ == "__main__":
    main()
