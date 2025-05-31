import cv2
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import supervision as sv
from inference_sdk import InferenceHTTPClient


class YoloDetector:
    def __init__(self, api_url, api_key, model_id, cloudinary_url, upload_preset):
        self.client = InferenceHTTPClient(api_url=api_url, api_key=api_key)
        self.model_id = model_id
        self.cloudinary_url = cloudinary_url
        self.upload_preset = upload_preset

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

    def detect_frame(self, frame: np.ndarray):
        height, width, _ = frame.shape

        # Convert BGR (OpenCV) to RGB for Cloudinary
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Encode frame as JPEG
        success, buffer = cv2.imencode(".jpg", rgb_frame)
        if not success:
            return frame, []

        # Upload to Cloudinary
        files = {"file": BytesIO(buffer.tobytes())}
        data = {"upload_preset": self.upload_preset}
        upload_res = requests.post(self.cloudinary_url, files=files, data=data)

        if upload_res.status_code != 200:
            print("Cloudinary upload failed:", upload_res.json())
            return frame, []

        image_url = upload_res.json().get("secure_url")
        if not image_url:
            return frame, []

        # Run inference using Roboflow
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
            return frame, []

        class_name_to_id = {name: idx for idx, name in enumerate(sorted(set(class_names)))}
        class_ids = np.array([class_name_to_id[name] for name in class_names], dtype=int)

        detections = sv.Detections(
            xyxy=np.array(xyxy),
            confidence=np.array(confidences),
            class_id=class_ids,
            data={"class_name": np.array(class_names)}
        )

        # Annotate frame
        annotated_frame = self.box_annotator.annotate(scene=frame.copy(), detections=detections)
        annotated_frame = self.label_annotator.annotate(scene=annotated_frame, detections=detections)

        # Prepare result list
        output_detections = []
        for i in range(len(detections.xyxy)):
            x1, y1, x2, y2 = map(int, detections.xyxy[i])
            x_center = (x1 + x2) // 2
            y_center = (y1 + y2) // 2
            location = self.get_location_label(x_center, y_center, width, height)

            class_name = detections.data['class_name'][i]
            conf = round(float(detections.confidence[i]), 2)

            output_detections.append((class_name, location, conf))

        return annotated_frame, output_detections


if __name__ == "__main__":
    detector = YoloDetector(
        api_url="https://detect.roboflow.com",
        api_key="BKDg8IoE7QqBivQ89Oyu",
        model_id="hose-jbybw/1",
        cloudinary_url="https://api.cloudinary.com/v1_1/dn8rj0auz/image/upload",
        upload_preset="sugar-2025"
    )

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Failed to open webcam.")
        exit()

    print("Press 'q' to quit.")
    frame_skip = 5
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame.")
            break

        # Run detection only every N frames
        if frame_count % frame_skip == 0:
            annotated_frame, detections = detector.detect_frame(frame)
        frame_count += 1

        # Show the annotated frame
        cv2.imshow("YOLO Detection", annotated_frame)

        # Print detections
        for label, location, conf in detections:
            print(f"Detected {label} at {location} with confidence {conf}")

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
