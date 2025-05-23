import os
import re
from io import BytesIO
import requests
from PIL import Image
from difflib import get_close_matches

CLOUDINARY_URL = "https://api.cloudinary.com/v1_1/dn8rj0auz/image/upload"
UPLOAD_PRESET = "sugar-2025"

def process_text_return_image_url(text, image_dir="data/static/images"):
    all_images = os.listdir(image_dir)
    uploaded_urls = {}

    def upload_to_cloudinary(filepath):
        with Image.open(filepath) as img:
            buffer = BytesIO()
            img.save(buffer, format=img.format)
            buffer.seek(0)
            files = {"file": buffer}
            data = {"upload_preset": UPLOAD_PRESET}
            response = requests.post(CLOUDINARY_URL, files=files, data=data)
            if response.status_code == 200:
                return response.json().get("secure_url")
            else:
                return None

    image_url = None

    def replacer(match):
        nonlocal image_url
        requested_filename = match.group(1)
        closest = get_close_matches(requested_filename, all_images, n=1)
        if not closest:
            return "[Missing image]"
        closest_file = closest[0]
        local_path = os.path.join(image_dir, closest_file)
        if closest_file not in uploaded_urls:
            url = upload_to_cloudinary(local_path)
            if url:
                uploaded_urls[closest_file] = url
                # Save only the first uploaded URL to return
                if image_url is None:
                    image_url = url
            else:
                return "[Upload failed]"
        else:
            if image_url is None:
                image_url = uploaded_urls[closest_file]
        return ""

    pattern = r"\[([\w\-]+\.(?:png|jpg|jpeg|gif))\]"
    new_text = re.sub(pattern, replacer, text)
    return new_text, image_url
