import requests
import os

model_id = '9098868e3b734826b7bc479604c31446'
out_dir = r"C:\Users\Admin\Documents\Default Project"

# Sketchfab CDN pattern for glb files
cdn_url = f"https://media.sketchfab.com/urls/{model_id}/dist/models"
headers = {'User-Agent': 'Mozilla/5.0'}

# Try the download endpoint without token
dl_url = f"https://api.sketchfab.com/v3/models/{model_id}/download"
r = requests.get(dl_url, headers=headers)
print(f"Download API: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    glb_url = data.get('glb', {}).get('url')
    if glb_url:
        print(f"Downloading from: {glb_url}")
        r2 = requests.get(glb_url, headers=headers)
        path = os.path.join(out_dir, "anime_boy_hoodie.glb")
        with open(path, 'wb') as f:
            f.write(r2.content)
        print(f"Saved: {path} ({len(r2.content)} bytes)")
    else:
        print(f"No GLB URL in response: {data}")
else:
    print(f"Response: {r.text[:500]}")
    
    # Try alternative: direct viewer URL approach
    print("\nTrying alternative download...")
    # Some models have a direct download format
    alt_url = f"https://sketchfab.com/api/v1/models/{model_id}/download"
    r3 = requests.get(alt_url, headers=headers, allow_redirects=True)
    print(f"Alt: {r3.status_code}, URL: {r3.url}")
