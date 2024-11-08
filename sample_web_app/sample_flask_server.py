from flask import Flask, request, jsonify
import cv2
import easyocr
from flask_cors import CORS
import numpy as np

app = Flask(__name__)
cors = CORS(app)
reader = easyocr.Reader(["en"], gpu=True)


def merge_boxes_once(detections, vertical_threshold, horizontal_threshold):
    """
    Perform one pass of merging bounding boxes that are close vertically
    and not far apart horizontally.
    """
    merged_boxes = []
    skip_indices = set()  # Track indices of boxes that have been merged

    for i, (bbox, text, score) in enumerate(detections):
        # Skip if this box has already been merged
        if i in skip_indices:
            continue

        x_min, y_min = bbox[0]
        x_max, y_max = bbox[2]
        found_merge = False

        for merged in merged_boxes:
            merged_bbox, merged_text, merged_score = merged
            merged_x_min, merged_y_min = merged_bbox[0]
            merged_x_max, merged_y_max = merged_bbox[2]

            # Check proximity only in the vertical direction and ensure horizontal alignment
            if (
                abs(y_min - merged_y_max) < vertical_threshold
                or abs(y_max - merged_y_min) < vertical_threshold
            ) and abs(x_min - merged_x_min) < horizontal_threshold:
                # Update the merged box to encompass both boxes vertically
                merged_bbox[0] = (min(merged_x_min, x_min), min(merged_y_min, y_min))
                merged_bbox[2] = (max(merged_x_max, x_max), max(merged_y_max, y_max))

                # Concatenate text and keep the highest score
                merged[1] = merged_text + " " + text  # Properly concatenate text
                merged[2] = max(merged_score, score)  # Update the score if needed
                found_merge = True
                break

        # If no close boxes were found, add as a new box
        if not found_merge:
            merged_boxes.append([bbox, text, score])
        else:
            # Mark the original box as merged to skip in future iterations
            skip_indices.add(i)

    return merged_boxes


def merge_boxes_until_stable(detections, vertical_threshold, horizontal_threshold):
    """
    Keep merging bounding boxes until no more merges are possible.
    """
    while True:
        # Perform one pass of merging
        merged_detections = merge_boxes_once(
            detections, vertical_threshold, horizontal_threshold
        )

        # Check if no new merges were made
        if len(merged_detections) == len(detections):
            break  # Stop if no boxes were merged in this pass

        # Update detections with merged results for the next pass
        detections = merged_detections

    return detections


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
    threshold = 0.1
    init_ver_thresh = 35
    init_hor_thresh = 35

    merged_detections = merge_boxes_until_stable(
        text_detections, init_ver_thresh, init_hor_thresh
    )

    # Prepare the response with bounding boxes and text
    response_data = []
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
