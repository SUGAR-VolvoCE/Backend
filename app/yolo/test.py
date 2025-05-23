from yolo_tool import detect_yolo

result = detect_yolo("https://res.cloudinary.com/dn8rj0auz/image/upload/v1747947996/grposvf3oxpei6ybrvh9.png")

print(result["annotated_image_url"])
for det in result["detections"]:
    print(det)
