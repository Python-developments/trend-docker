import os
import requests
import tempfile
from django.core.files.base import File

from celery import shared_task
from io import BytesIO
from PIL import Image
from moviepy.editor import VideoFileClip

from vlog.models import Video

@shared_task()
def create_video_thumbnail(video_pk):
    video_obj = Video.objects.get(pk=video_pk)
    # Extract a frame from the video (at 1 second, or earlier if the video is shorter)
    try:
        # Download the video temporarily for processing
        with tempfile.NamedTemporaryFile(delete=True, suffix='.mp4') as temp_file:
            response = requests.get(video_obj.video.url, stream=True)
            if response.status_code == 200:
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                temp_file.flush()
            # Process the video to extract a frame for the thumbnail
            with VideoFileClip(temp_file.name) as video:
                duration = video.duration
                thumbnail_time = min(1, duration)  # Take a frame at 1 second or earlier if shorter
                frame = video.get_frame(thumbnail_time)
                
                # Convert frame to an image
                image = Image.fromarray(frame)
                image.thumbnail((160, 160))  # Resize thumbnail
                
                # Save the image to an in-memory file
                img_temp = BytesIO()
                image.save(img_temp, format="PNG")
                img_temp.seek(0)
                
                # Save the thumbnail to the Video model
                thumbnail_filename = f"thumbnails/{os.path.basename(video_obj.video.name).split('.')[0]}.png"
                video_obj.thumbnail.save(thumbnail_filename, File(img_temp), save=False)
                video_obj.save(update_fields=['thumbnail'])
    except Exception as e:
        print("some errors while generate thumbnail", e)