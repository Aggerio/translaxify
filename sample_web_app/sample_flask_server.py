from flask import Flask, request, jsonify
import cv2
import easyocr
from flask_cors import CORS, cross_origin
import numpy as np

app = Flask(__name__)
cors = CORS(app)
reader = easyocr.Reader(["en"], gpu=True)


def merge_boxes(detections, distance_threshold=30):
    """
    Merge bounding boxes that are close to each other.
    """
    merged_boxes = []
    for bbox, text, score in detections:
        x_min, y_min = bbox[0]
        x_max, y_max = bbox[2]

        # Find overlapping or close boxes to merge
        found_merge = False
        for merged in merged_boxes:
            (merged_bbox, merged_text, merged_score) = merged
            merged_x_min, merged_y_min = merged_bbox[0]
            merged_x_max, merged_y_max = merged_bbox[2]

            # Calculate the distance between boxes
            if (
                abs(merged_x_min - x_min) < distance_threshold
                and abs(merged_y_min - y_min) < distance_threshold
            ):
                # Update the merged box to include the new one
                merged_bbox[0] = (min(merged_x_min, x_min), min(merged_y_min, y_min))
                merged_bbox[2] = (max(merged_x_max, x_max), max(merged_y_max, y_max))
                merged_text += " " + text
                merged_score = max(merged_score, score)
                found_merge = True
                break

        # If no close boxes, add as new
        if not found_merge:
            merged_boxes.append([bbox, text, score])

    return merged_boxes


@app.route("/process_image", methods=["POST"])
def process_image():
    # Check if an image file is provided
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    # Load the image from the request
    file = request.files["image"]
    np_img = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    # Error handling if image is not loaded
    if img is None:
        return jsonify({"error": "Invalid image format"}), 400

    # Perform OCR on the image
    text_detections = reader.readtext(img)
    merged_detections = merge_boxes(text_detections)

    # Prepare the response with bounding boxes and text
    response_data = []
    threshold = 0.10
    for bbox, text, score in merged_detections:
        if score > threshold:  # Apply threshold filter
            box = {
                "bbox": [list(map(int, bbox[0])), list(map(int, bbox[2]))],
                "text": text,
                "score": score,
            }
            response_data.append(box)

    return jsonify(response_data)


if __name__ == "__main__":
    app.run(debug=True)
