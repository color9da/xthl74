import os
import requests
import time
import json
import random
import string
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def upload_to_youtube(video_path, title, description, tags=None, privacy_status="public"):
    print("\n" + "=" * 60)
    print("YOUTUBE SHORTS UPLOAD STARTING")
    print("=" * 60)
    
    client_id = os.getenv('YT_CLIENT_ID')
    client_secret = os.getenv('YT_CLIENT_SECRET')
    refresh_token = os.getenv('YT_REFRESH_TOKEN')
    
    if not all([client_id, client_secret, refresh_token]):
        raise ValueError("Missing YouTube credentials")
    
    def mask(s):
        if not s: return 'NONE'
        return s[:10] + '...' + s[-4:] if len(s) > 15 else s[:6] + '...'
    
    print(f"[youtube] Client ID: {mask(client_id)}")
    print(f"[youtube] Refresh Token: {mask(refresh_token)}")
    
    # Get access token from refresh token
    print("[youtube] Getting access token...")
    token_resp = requests.post('https://oauth2.googleapis.com/token', data={
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }, timeout=30)
    
    if token_resp.status_code != 200:
        raise Exception(f"Token refresh failed: {token_resp.text[:200]}")
    
    access_token = token_resp.json()['access_token']
    print("[youtube] Access token obtained")
    
    # Upload video
    print(f"[youtube] Uploading: {video_path}")
    
    boundary = '----' + ''.join(random.choices(string.ascii_letters + string.digits, k=30))
    
    if tags is None:
        tags = []
    
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': '22'  # People & Blogs
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False
        }
    }
    
    body_bytes = json.dumps(body).encode('utf-8')
    
    with open(video_path, 'rb') as f:
        video_data = f.read()
    
    # Build multipart body
    parts = []
    parts.append(b'--' + boundary.encode())
    parts.append(b'Content-Type: application/json; charset=UTF-8')
    parts.append(b'')
    parts.append(body_bytes)
    parts.append(b'--' + boundary.encode())
    parts.append(b'Content-Type: video/mp4')
    parts.append(b'Content-Transfer-Encoding: binary')
    parts.append(b'')
    parts.append(video_data)
    parts.append(b'--' + boundary.encode() + b'--')
    
    data = b'\r\n'.join(parts)
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': f'multipart/related; boundary={boundary}',
        'Content-Length': str(len(data))
    }
    
    upload_resp = requests.post(
        'https://www.googleapis.com/upload/youtube/v3/videos?part=snippet,status&uploadType=multipart',
        headers=headers, data=data, timeout=600
    )
    
    if upload_resp.status_code == 200:
        video_id = upload_resp.json().get('id', 'N/A')
        print(f"[youtube] SUCCESS! Video ID: {video_id}")
        print(f"[youtube] https://www.youtube.com/watch?v={video_id}")
        return {'id': video_id, 'platform': 'youtube', 'status': 'success'}
    else:
        raise Exception(f"YouTube upload failed ({upload_resp.status_code}): {upload_resp.text[:500]}")
