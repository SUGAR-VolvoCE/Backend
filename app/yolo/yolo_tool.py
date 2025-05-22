import requests
from PIL import Image
from io import BytesIO
from ultralytics import YOLO
import cv2
import numpy as np

CLOUDINARY_URL = "https://api.cloudinary.com/v1_1/dn8rj0auz/image/upload"
UPLOAD_PRESET = "sugar-2025"

LABEL_MAP = {
    "Corrosion": "Corrosion",
    "Desgaste_Manguera": "Hose Wear",
    "Falla_Piston": "Piston Failure",
    "Humedecimiento": "Moisture Ingress"
}

# Carrega os dois modelos
model_best = YOLO("app/yolo/best.pt")
model_wire = YOLO("app/yolo/wire.pt")

def get_location_label(x_center, y_center, width, height):
    if x_center < width / 3:
        horiz = "left"
    elif x_center < 2 * width / 3:
        horiz = "center"
    else:
        horiz = "right"

    if y_center < height / 3:
        vert = "top"
    elif y_center < 2 * height / 3:
        vert = "middle"
    else:
        vert = "bottom"

    return f"{vert}-{horiz}"

def detect_yolo(image_url):
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content)).convert('RGB')
    img_array = np.array(img)
    height, width, _ = img_array.shape

    results_best = model_best(img)[0]
    results_wire = model_wire(img)[0]

    detections = []

    for box in results_best.boxes:
        conf = float(box.conf)
        cls_id = int(box.cls)
        class_name = model_best.names[cls_id]
        print(class_name)

        if conf >= 0.25:
            english_label = LABEL_MAP.get(class_name, class_name)
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            x_center = (x1 + x2) // 2
            y_center = (y1 + y2) // 2
            location = get_location_label(x_center, y_center, width, height)

            detections.append({
                "label": english_label,
                "location": location,
                "confidence": round(conf, 2),
                "box": {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
            })

            cv2.rectangle(img_array, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img_array, english_label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    for box in results_wire.boxes:
        conf = float(box.conf)
        cls_id = int(box.cls)
        class_name = model_wire.names[cls_id]
        print("CLASS: ", class_name)

        if conf >= 0.25:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            x_center = (x1 + x2) // 2
            y_center = (y1 + y2) // 2
            location = get_location_label(x_center, y_center, width, height)

            detections.append({
                "label": class_name,  # mantém o nome original
                "location": location,
                "confidence": round(conf, 2),
                "box": {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
            })

            label_text = f"Wire: {class_name}"
            cv2.rectangle(img_array, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(img_array, label_text, (x1, y2 + 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)


    is_success, buffer = cv2.imencode(".jpg", cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR))
    if not is_success:
        return {"error": "Failed to encode annotated image"}

    files = {"file": BytesIO(buffer.tobytes())}
    data = {"upload_preset": UPLOAD_PRESET}
    upload_res = requests.post(CLOUDINARY_URL, files=files, data=data)

    if upload_res.status_code != 200:
        return {"error": "Cloudinary upload failed", "details": upload_res.json()}

    annotated_url = upload_res.json().get("secure_url")

    return {
        "detections": [(det["label"], det["location"]) for det in detections],
        "annotated_image_url": annotated_url
    }
