from yolo_tool import detect_yolo

result = detect_yolo("https://i.postimg.cc/LX3KKCZb/test2.jpg")

print(result["annotated_image_url"])
for det in result["detections"]:
    print(det)
