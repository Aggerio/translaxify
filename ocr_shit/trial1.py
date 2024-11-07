import cv2
import easyocr
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import pprint


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


def draw_bounding_boxes(image, detections, threshold):
    """Draw bounding boxes on the image based on the threshold."""
    img_copy = image.copy()  # Work on a copy of the image
    for bbox, text, score in detections:
        if score >= threshold:
            cv2.rectangle(
                img_copy,
                tuple(map(int, bbox[0])),
                tuple(map(int, bbox[2])),
                (0, 255, 0),
                2,
            )
            cv2.putText(
                img_copy,
                text,
                tuple(map(int, bbox[0])),
                cv2.FONT_HERSHEY_COMPLEX_SMALL,
                0.65,
                (255, 0, 0),
                2,
            )
    return img_copy


# Load image and initialize OCR
image_path = "trial_image.jpg"
img = cv2.imread(image_path)
if img is None:
    raise ValueError("Error loading the image. Please check the file path.")

reader = easyocr.Reader(["pt"], gpu=True)
text_detections = reader.readtext(img)
pprint.pprint(text_detections)

# Initial parameters
initial_threshold = 0.10
initial_vertical_threshold = 5
initial_horizontal_threshold = 50

# Merge bounding boxes until no further merges are possible
text_detections = merge_boxes_until_stable(
    text_detections, initial_vertical_threshold, initial_horizontal_threshold
)

# Create the plot
fig, ax = plt.subplots()
plt.subplots_adjust(left=0.1, bottom=0.4)

# Display image with bounding boxes at initial threshold
display_img = draw_bounding_boxes(img, text_detections, initial_threshold)
im_display = ax.imshow(cv2.cvtColor(display_img, cv2.COLOR_BGR2RGBA))

# Add sliders for threshold adjustment
ax_threshold_slider = plt.axes(
    [0.2, 0.25, 0.65, 0.03], facecolor="lightgoldenrodyellow"
)
threshold_slider = Slider(
    ax_threshold_slider,
    "Score Threshold",
    0.0,
    1.0,
    valinit=initial_threshold,
    valstep=0.01,
)

ax_vertical_slider = plt.axes([0.2, 0.15, 0.65, 0.03], facecolor="lightblue")
vertical_slider = Slider(
    ax_vertical_slider,
    "Vertical Threshold",
    0,
    50,
    valinit=initial_vertical_threshold,
    valstep=1,
)

ax_horizontal_slider = plt.axes([0.2, 0.05, 0.65, 0.03], facecolor="lightgreen")
horizontal_slider = Slider(
    ax_horizontal_slider,
    "Horizontal Threshold",
    0,
    100,
    valinit=initial_horizontal_threshold,
    valstep=1,
)


# Update function to redraw bounding boxes based on slider values
def update(val):
    # Get the current values of all sliders
    threshold = threshold_slider.val
    vertical_threshold = vertical_slider.val
    horizontal_threshold = horizontal_slider.val

    # Re-merge boxes based on the new vertical and horizontal thresholds
    merged_detections = merge_boxes_until_stable(
        text_detections, vertical_threshold, horizontal_threshold
    )

    # Draw bounding boxes with the updated merged detections and score threshold
    updated_img = draw_bounding_boxes(img, merged_detections, threshold)
    im_display.set_data(cv2.cvtColor(updated_img, cv2.COLOR_BGR2RGBA))
    fig.canvas.draw_idle()


# Attach the update function to the sliders
threshold_slider.on_changed(update)
vertical_slider.on_changed(update)
horizontal_slider.on_changed(update)

plt.show()
