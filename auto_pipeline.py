import os, sys, random, json
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_published_history():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return []
    return []

def get_repost_counts():
    history = get_published_history()
    counts = {}
    for entry in history:
        vn = entry.get('video_name', '')
        counts[vn] = counts.get(vn, 0) + 1
    return counts

def select_random_processed_video():
    if not os.path.exists(PROCESSED_DIR):
        print("No Processed_Videos folder")
        return None
    all_videos = [f for f in os.listdir(PROCESSED_DIR) if f.endswith('.mp4')]
    if not all_videos:
        print("No processed videos found")
        return None
    repost_counts = get_repost_counts()
    weights = []
    for vid in all_videos:
        count = repost_counts.get(vid, 0)
        weight = max(1, 1000 // (3 ** count))
        weights.append(weight)
    selected = random.choices(all_videos, weights=weights, k=1)[0]
    selected_path = os.path.join(PROCESSED_DIR, selected)
    post_count = repost_counts.get(selected, 0)
    print(f"Selected (posted {post_count}x before): {selected}")
    return selected_path

def run_pipeline():
    print("\n" + "=" * 60)
    print("YOUTUBE SHORTS AUTOMATION PIPELINE")
    print("=" * 60 + "\n")

    print("STEP 1: Fetching video from Dropbox...")
    from dropbox_fetch import fetch_one_video_from_dropbox
    downloaded = fetch_one_video_from_dropbox(allow_repost=False)
    if not downloaded:
        print("\nNo new videos in Dropbox")
        print("REPOST MODE: Fetching random published video...\n")
        downloaded = fetch_one_video_from_dropbox(allow_repost=True)
        if not downloaded:
            print("No videos to post. Pipeline complete.")
            return
        print("Repost Mode: Using existing video\n")
    print("Step 1 complete\n")

    print("STEP 2: Processing video...")
    from process_videos import process_single_video
    processed = process_single_video(downloaded)
    if not processed or not os.path.exists(processed):
        print("Video processing failed!")
        sys.exit(1)
    print("Step 2 complete\n")

    print("STEP 3: Uploading to YouTube...")
    print("=" * 60 + "\n")
    from daily_publisher import main as publish_video
    sys.argv = ["daily_publisher.py", processed]
    publish_video()

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    run_pipeline()
