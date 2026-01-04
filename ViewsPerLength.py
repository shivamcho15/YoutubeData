from googleapiclient.discovery import build
import matplotlib.pyplot as plt
from datetime import datetime
import isodate
from config import API_KEY, CHANNEL_ID

# Build YouTube client
youtube = build("youtube", "v3", developerKey=API_KEY)

# 1️⃣ Get uploads playlist ID
channel_response = youtube.channels().list(
    part="contentDetails,snippet",
    id=CHANNEL_ID
).execute()

uploads_playlist_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
channel_name = channel_response["items"][0]["snippet"]["title"]

# 2️⃣ Get all video IDs
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
        video_ids.append(item["snippet"]["resourceId"]["videoId"])

    next_page_token = response.get("nextPageToken")
    if not next_page_token:
        break

print(f"Fetched {len(video_ids)} videos")

# 3️⃣ Fetch video stats in batches
lengths = []
views = []

for i in range(0, len(video_ids), 50):
    batch = video_ids[i:i + 50]

    stats_response = youtube.videos().list(
        part="contentDetails,statistics",
        id=",".join(batch)
    ).execute()

    for item in stats_response["items"]:
        stats = item["statistics"]
        content = item["contentDetails"]

        if "viewCount" not in stats:
            continue

        view_count = int(stats["viewCount"])

        # Convert ISO 8601 duration → minutes
        duration = isodate.parse_duration(content["duration"]).total_seconds() / 60

        lengths.append(duration)
        views.append(view_count)

# 4️⃣ Plot scatter plot
plt.figure(figsize=(10, 6))
plt.scatter(lengths, views, alpha=0.6)
plt.xlabel("Video Length (minutes)")
plt.ylabel("Views")
plt.title(f"Views vs Video Length for {channel_name}")
plt.grid(True, linestyle="--", alpha=0.5)

plt.ticklabel_format(axis="y", style="plain", useOffset=False)


plt.tight_layout()
plt.show()
