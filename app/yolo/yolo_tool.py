import requests
from PIL import Image
from io import BytesIO
import cv2
import numpy as np
import supervision as sv
from inference_sdk import InferenceHTTPClient

class YoloDetector:
    def __init__(self, api_url, api_key, model_id, cloudinary_url, upload_preset):
        self.client = InferenceHTTPClient(api_url=api_url, api_key=api_key)
        self.model_id = model_id
        self.cloudinary_url = cloudinary_url
        self.upload_preset = upload_preset

        # Annotators initialized once
        self.box_annotator = sv.BoxAnnotator()
        self.label_annotator = sv.LabelAnnotator()

    def get_location_label(self, x_center, y_center, width, height):
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

    def detect_yolo(self, image_url):
        # Load image from URL
        print("before")
        response = requests.get(image_url)
        print("after")

        img = Image.open(BytesIO(response.content)).convert('RGB')
        img_array = np.array(img)
        height, width, _ = img_array.shape

        # Inference
        results = self.client.infer(image_url, model_id=self.model_id)

        xyxy = []
        confidences = []
        class_names = []

        for pred in results['predictions']:
            x1 = int(pred['x'] - pred['width'] / 2)
            y1 = int(pred['y'] - pred['height'] / 2)
            x2 = int(pred['x'] + pred['width'] / 2)
            y2 = int(pred['y'] + pred['height'] / 2)

            xyxy.append([x1, y1, x2, y2])
            confidences.append(pred['confidence'])
            class_names.append(pred['class'])

        if not xyxy:
            return {"detections": [], "annotated_image_url": None}

        class_name_to_id = {name: idx for idx, name in enumerate(sorted(set(class_names)))}
        class_ids = np.array([class_name_to_id[name] for name in class_names], dtype=int)

        detections = sv.Detections(
            xyxy=np.array(xyxy),
            confidence=np.array(confidences),
            class_id=class_ids,
            data={"class_name": np.array(class_names)}
        )

        output_detections = []

        for i in range(len(detections.xyxy)):
            x1, y1, x2, y2 = map(int, detections.xyxy[i])
            x_center = (x1 + x2) // 2
            y_center = (y1 + y2) // 2
            location = self.get_location_label(x_center, y_center, width, height)

            class_name = detections.data['class_name'][i]
            conf = round(float(detections.confidence[i]), 2)

            output_detections.append({
                "label": class_name,
                "location": location,
                "confidence": conf,
                "box": {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
            })

        # Annotate
        annotated_image = self.box_annotator.annotate(scene=img_array.copy(), detections=detections)
        annotated_image = self.label_annotator.annotate(scene=annotated_image, detections=detections)

        # Upload annotated image to Cloudinary
        is_success, buffer = cv2.imencode(".jpg", cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
        if not is_success:
            return {"error": "Failed to encode annotated image"}

        files = {"file": BytesIO(buffer.tobytes())}
        data = {"upload_preset": self.upload_preset}
        upload_res = requests.post(self.cloudinary_url, files=files, data=data)

        if upload_res.status_code != 200:
            return {"error": "Cloudinary upload failed", "details": upload_res.json()}

        annotated_url = upload_res.json().get("secure_url")

        return {
            "detections": [(det["label"], det["location"], det["confidence"]) for det in output_detections],
            "annotated_image_url": annotated_url
        }


# Usage example:
if __name__ == "__main__":
    detector = YoloDetector(
        api_url="https://detect.roboflow.com",
        api_key="BKDg8IoE7QqBivQ89Oyu",
        model_id="hose-jbybw/1",
        cloudinary_url="https://api.cloudinary.com/v1_1/dn8rj0auz/image/upload",
        upload_preset="sugar-2025"
    )

    # You can now call detect_yolo many times efficiently:
    urls = [
        "https://i.postimg.cc/QtyYXmfW/mangueira.jpg",
        # add more URLs here
    ]

    for url in urls:
        result = detector.detect_yolo(url)
        print(result)
