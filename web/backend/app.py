from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import torch
import torchvision.transforms as T
import torchvision
from PIL import Image
import numpy as np
import cv2
import json
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.models.detection.mask_rcnn import MaskRCNNPredictor
import io
from vp_detection import get_vp_inliers, save_visualizations
import tempfile



app = FastAPI(redirect_slashes=False)

#Modify the CORS settings to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the trained model globally
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
def preprocess_image(image_data):
    transform = T.ToTensor()
    image = Image.open(io.BytesIO(image_data)).convert("RGB")
    return transform(image).unsqueeze(0)  # add batch dimension

# Prediction function
def predict_and_linearize(model, image_data, device, threshold=0.5, target_class_id=10):
    image = Image.open(io.BytesIO(image_data)).convert("RGB")
    input_image = preprocess_image(image_data).to(device)

    with torch.no_grad():
        outputs = model(input_image)

    # Extract data from outputs
    image_np = np.array(image)
    results = []
    boxes = outputs[0]['boxes'].cpu().detach().numpy()
    labels = outputs[0]['labels'].cpu().detach().numpy()
    scores = outputs[0]['scores'].cpu().detach().numpy()
    masks = outputs[0]['masks'].cpu().detach().numpy()

    for i, score in enumerate(scores):
        if score >= threshold and labels[i] == target_class_id:
            box = boxes[i].astype(int)
            mask = masks[i][0] > 0.5
            contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            linearized_contours = []

            valid_prediction = True  # Flag to check if the prediction should be kept

            for contour in contours:
                # Approximate contour with linear segments
                epsilon = 0.04 * cv2.arcLength(contour, True)  # Approximation factor
                approx = cv2.approxPolyDP(contour, epsilon, True)

                if len(approx) != 4:
                    valid_prediction = False  # Discard the prediction if any contour has more than 4 points
                    break

                linearized_contours.append(approx.reshape(-1, 2).tolist())  # Flatten contour to list of points

            if not valid_prediction:
                continue  # Skip this prediction entirely

            results.append({
                "class_id": int(labels[i]),
                "score": float(score),
                "bounding_box": box.tolist(),
                "linearized_contours": linearized_contours
            })

    return results

# Initialize the model
device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
weights_path = "models/best_model.pth"  # Replace with your weights file path
num_classes = 12  # Adjust according to your model
model = load_model(weights_path, num_classes, device)

@app.post("/predict/")
async def predict(file: UploadFile = File(...), threshold: float = 0.5, target_class_id: int = 10):
    try:
        image_data = await file.read()
        results = predict_and_linearize(model, image_data, device, threshold, target_class_id)

        # Return results as JSON
        return JSONResponse(content={"predictions": results})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/detect-vanishing-points/")
async def detect_vanishing_points(file: UploadFile = File(...),
                                   sigma: float = 5.0,
                                   iterations: int = 3000,
                                   line_len: int = 11,
                                   line_gap: int = 7,
                                   threshold: float = 2.0):
    try:
        # Save uploaded file temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(await file.read())
        temp_file.close()

        # Process image
        inlier_lines_list, hypothesis_list, image, edges, lines = get_vp_inliers(
            temp_file.name, sigma, iterations, line_len, line_gap, threshold
        )

        # Save visualizations
        colors = ['r', 'g', 'b']
        visualization_path = save_visualizations(image, edges, lines, inlier_lines_list, hypothesis_list, colors)

        # Prepare JSON response
        vanishing_points = [
            {"x": vp[0], "y": vp[1]} for vp in hypothesis_list
        ]

        response = {
            "vanishing_points": vanishing_points,
            "visualization_path": visualization_path
        }

        return JSONResponse(content=response)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

