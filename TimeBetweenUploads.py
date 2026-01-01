from googleapiclient.discovery import build
from datetime import datetime
import matplotlib.pyplot as plt
from config import API_KEY, CHANNEL_ID


# API_KEY = "INSERT_API_KEY"
# CHANNEL_ID = "INSERT_CHANNEL_ID"

youtube = build("youtube", "v3", developerKey=API_KEY)

# --- 1. Get uploads playlist ID ---
channel_response = youtube.channels().list(
    part="contentDetails",
    id=CHANNEL_ID
).execute()

uploads_playlist_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

# --- 2. Paginate uploads ---
video_meta = {}
video_ids = []
next_page_token = None

while True:
    response = youtube.playlistItems().list(
        part="snippet",
        playlistId=uploads_playlist_id,
        maxResults=50,
        pageToken=next_page_token
    ).execute()

    for item in response["items"]:
        vid = item["snippet"]["resourceId"]["videoId"]
        video_ids.append(vid)
        video_meta[vid] = {
            "published": item["snippet"]["publishedAt"]
        }


    next_page_token = response.get("nextPageToken")
    if not next_page_token:
        break

# --- 3. Fetch statistics ---
dates = []
data = []

for i in range(0, len(video_ids), 50):
    print(i)
    batch = video_ids[i:i + 50]

    stats_response = youtube.videos().list(
        part="statistics",
        id=",".join(batch)
    ).execute()

    for item in stats_response["items"]:
        stats = item["statistics"]

        views = int(stats.get("viewCount", 0))
        likes = int(stats.get("likeCount", 0))

        if views == 0:
            continue

        ratio = likes / views

        published = datetime.fromisoformat(
            video_meta[item["id"]]["published"].replace("Z", "+00:00")
        )

        dates.append(published)
        if(len(dates)>1):
            
            difference_in_time = abs((dates[-1] - dates[-2]).total_seconds() / 86400)
            data.append(difference_in_time)

        else:
            data.append(0)
        

# --- 4. Sort by date ---
combined = sorted(zip(dates, data), key=lambda x: x[0])
dates, data = zip(*combined)

# --- 5. Plot ---
plt.figure(figsize=(14, 6))
plt.bar(dates, data, width=2)
plt.xlabel("Publish Date")
plt.ylabel("Avg Time Between Uploads")
plt.title("Upload Frequency Over Time")

# Scale y-axis so tallest bar nearly hits top
max_data = max(data)
plt.ylim(0, max_data * 1.05)
import numpy as np
y_lines = np.arange(0, max_data + 2, 2)  # 0, 2, 4, ...
plt.yticks(y_lines)                       # Set ticks
plt.grid(axis='y', linestyle='--', alpha=0.5)  # Draw horizontal grid lines

plt.ticklabel_format(axis="y", style="plain", useOffset=False)

plt.tight_layout()
plt.show()

