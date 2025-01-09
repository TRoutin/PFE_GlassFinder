import torch
import torchvision
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.models.detection.mask_rcnn import MaskRCNNPredictor
import torchvision.transforms as T
from tkinter import Tk, filedialog
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import cv2
import json

# Load the trained model with the specified number of classes
def load_model(weights_path, num_classes, device):
    model = torchvision.models.detection.maskrcnn_resnet50_fpn(weights=None)
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
    in_features_mask = model.roi_heads.mask_predictor.conv5_mask.in_channels
    hidden_layer = 256
    model.roi_heads.mask_predictor = MaskRCNNPredictor(in_features_mask, hidden_layer, num_classes)

    # Load weights and set model to evaluation mode
    model.load_state_dict(torch.load(weights_path, map_location=device))
    model.to(device).eval()
    return model

# Preprocess the image
def preprocess_image(image_path):
    image = Image.open(image_path).convert("RGB")
    transform = T.ToTensor()
    return transform(image).unsqueeze(0)  # add batch dimension

# Display predictions on the image and save linearized contours to a JSON file
def display_predictions(image, outputs, threshold=0.5, target_class_id=10, output_json="linearized_masks.json"):
    image_np = np.array(image)
    results = []  # List to store linearized mask data

    # Extract boxes, labels, and masks from outputs
    boxes = outputs[0]['boxes'].cpu().detach().numpy()
    labels = outputs[0]['labels'].cpu().detach().numpy()
    scores = outputs[0]['scores'].cpu().detach().numpy()
    masks = outputs[0]['masks'].cpu().detach().numpy()

    for i, score in enumerate(scores):
        if score >= threshold and labels[i] == target_class_id:  # Check if the prediction is of the target class
            box = boxes[i].astype(int)
            mask = masks[i][0] > 0.5  # Convert mask to binary format
            label = labels[i]

            # Extract contours
            contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            linearized_contours = []

            valid_prediction = True  # Flag to check if the prediction should be kept

            for contour in contours:
                # Approximate contour with linear segments
                epsilon = 0.04 * cv2.arcLength(contour, True)  # Approximation factor
                approx = cv2.approxPolyDP(contour, epsilon, True)

                if len(approx) > 4:
                    valid_prediction = False  # Discard the prediction if any contour has more than 4 points
                    break

                linearized_contours.append(approx.reshape(-1, 2).tolist())  # Flatten contour to list of points

            if not valid_prediction:
                continue  # Skip this prediction entirely

            # Draw the linearized contour on the image
            for approx in linearized_contours:
                cv2.polylines(image_np, [np.array(approx, np.int32)], True, (0, 255, 0), 2)

            # Append to results list
            results.append({
                "class_id": int(label),
                "score": float(score),
                "bounding_box": box.tolist(),
                "linearized_contours": linearized_contours
            })

            # Draw bounding box for reference
            cv2.rectangle(image_np, (box[0], box[1]), (box[2], box[3]), (255, 0, 0), 2)
            # Display label and score
            cv2.putText(image_np, f"Class: {label}, Score: {score:.2f}", (box[0], box[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    # Save the results to a JSON file
    with open(output_json, "w") as f:
        json.dump(results, f, indent=4)

    # Show the image with predictions for the target class
    plt.figure(figsize=(10, 10))
    plt.imshow(image_np)
    plt.axis("off")
    plt.show()

# Main function to test the model on a single image
def main(image_path, weights_path, num_classes=12, threshold=0.5):
    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")

    # Load the model and image
    model = load_model(weights_path, num_classes, device)
    image = Image.open(image_path).convert("RGB")
    input_image = preprocess_image(image_path).to(device)

    # Run the model
    with torch.no_grad():
        outputs = model(input_image)

    # Display predictions and save linearized contours to JSON
    display_predictions(image, outputs, threshold)

if __name__ == "__main__":
    root = Tk()
    root.withdraw()  # Masquer la fenêtre principale de Tkinter
    
    image_path = filedialog.askopenfilename(title="Choisir une image",
                                            filetypes=[("Images", "*.jpg;*.jpeg;*.png;*.bmp")])
    weights_path = "best_model3.pth"  # Path to the saved model weights
    main(image_path, weights_path)
