from models import *
from utils.utils import *
from utils.datasets import *

from PIL import Image

import torch
import torchvision.transforms as transforms

import argparse


if __name__ == "__main__":
  # Get arguments.
  parser = argparse.ArgumentParser()
  parser.add_argument("--pth", help="the path to your image file")
  args = parser.parse_args()

  # Get the GPU sources.
  device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

  # Set up model
  model = Darknet('config/yolov3.cfg', img_size=416).to(device)
  # Load darknet weights
  model.load_darknet_weights('weights/yolov3.weights')
  # Set in evaluation mode
  model.eval()

  classes = load_classes('data/coco.names')  # Extracts class labels from file

  # Configure input
  origin_img = Image.open(args.pth)
  img = transforms.ToTensor()(origin_img)
  origin_shape = img.shape[1:]
  img, _ = pad_to_square(img, 0)    # Pad to square resolution
  img = resize(img, 416)[None, :, :, :]  # Resize
  img = img.to(device)

  # Get detections
  with torch.no_grad():
    detections = model(img)
    detections = non_max_suppression(detections, 0.8, 0.4)[0]

  if detections is not None:
    # Rescale boxes to original image
    detections = rescale_boxes(detections, 416, origin_shape)
    for x1, y1, x2, y2, conf, cls_conf, cls_pred in detections:
      if cls_pred not in [0, 15, 16]: # Only detect person, cat and dog.
        continue
      print(f'{x1} {y1} {x2} {y2}')
      box_w = x2 - x1
      box_h = y2 - y1