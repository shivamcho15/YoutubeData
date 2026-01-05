from googleapiclient.discovery import build
import matplotlib.pyplot as plt
from datetime import datetime, timezone
import isodate
import requests
from PIL import Image
from io import BytesIO
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

from config import API_KEY, CHANNEL_ID

#CHOOSE PROPERTIES
X_PROPERTY = "duration_minutes"
Y_PROPERTY = "views"

youtube = build("youtube", "v3", developerKey=API_KEY)

#GET INFO
channel_response = youtube.channels().list(
    part="contentDetails,snippet",
    id=CHANNEL_ID
).execute()

channel_snippet = channel_response["items"][0]["snippet"]
channel_name = channel_snippet["title"]
uploads_playlist_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

#PROFILE PIC
profile_pic_url = channel_snippet["thumbnails"]["high"]["url"]
img_response = requests.get(profile_pic_url)
profile_img = Image.open(BytesIO(img_response.content))

#GET VIDEO IDS
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

#VIDEO DATA
videos = []

for i in range(0, len(video_ids), 50):
    batch = video_ids[i:i + 50]

    response = youtube.videos().list(
        part="statistics,contentDetails,snippet",
        id=",".join(batch)
    ).execute()

    for item in response["items"]:
        stats = item.get("statistics", {})
        content = item["contentDetails"]
        snippet = item["snippet"]

        views = int(stats.get("viewCount", 0))
        if views == 0:
            continue

        likes = int(stats.get("likeCount", 0))

        age_days = max(
    1,
    (
        datetime.now(timezone.utc)
        - datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00"))
    ).days
)

        video = {
        "views": views,
        "likes": likes,
        "comments": int(stats.get("commentCount", 0)),

        "duration_minutes": isodate.parse_duration(
            content["duration"]
        ).total_seconds() / 60,

        "duration_seconds": isodate.parse_duration(
            content["duration"]
        ).total_seconds(),

        "published_days_ago": age_days,

        "like_ratio": likes / views,

        "engagement_rate": (likes + int(stats.get("commentCount", 0))) / views,

        "views_per_day": views / age_days,

        "likes_per_1k_views": likes / views * 1000,

        "comments_per_1k_views": int(stats.get("commentCount", 0)) / views * 1000,

        "title_length": len(snippet["title"]),
        "title_word_count": len(snippet["title"].split())}

        videos.append(video)

print(f"Usable videos: {len(videos)}")

#PROPERTIES
def extract(prop):
    return [v[prop] for v in videos if prop in v]

x = extract(X_PROPERTY)
y = extract(Y_PROPERTY)


plt.figure(figsize=(12, 7))
plt.scatter(x, y, alpha=0.6)

plt.xlabel(X_PROPERTY.replace("_", " ").title())
plt.ylabel(Y_PROPERTY.replace("_", " ").title())
plt.title(f"{Y_PROPERTY.replace('_',' ').title()} vs {X_PROPERTY.replace('_',' ').title()}\n{channel_name}")

plt.grid(True, linestyle="--", alpha=0.5)
plt.ticklabel_format(axis="y", style="plain", useOffset=False)

#DISPLAY PROFILE PIC
imagebox = OffsetImage(profile_img, zoom=0.04)

ab = AnnotationBbox(
    imagebox,
    (0.05, 1.06),          # top-left
    xycoords="axes fraction",
    frameon=False
)

plt.gca().add_artist(ab)

plt.tight_layout()
plt.show()
