import cv2
import time
import numpy as np


class Yolov3:

    def __init__(self, config="Yolo_config/yolov3.cfg",
        weights="Yolo_config/yolov3.weights"):
        self.img_resize = (416, 416)    # Same as the setting in `yolov3.cfg`.
        # Build Yolo_v3 network.
        self.yolo = cv2.dnn.readNetFromDarknet("yolov3.cfg", "yolov3.weights")
        # Determine only the *output* layer names that we need from YOLO.
        self.ln = [self.yolo.getLayerNames()[i[0] - 1] \
            for i in self.yolo.getUnconnectedOutLayers()]
        # The predicted bounding boxes and class ids.
        self.boxes = [] # [x, y, w, h]
        self.ids = []
        # To check whether it's the latest data.
        self.time_stamp = time.time()


    # @img: the input image array. The order of its channel should be RGB.
    # @nms_thresh: threshold for non-maximum suppression.
    def predict(self, img, score_thresh=0.5, nms_thresh=0.5):
        h, w = img.shape[:2]

        # Construct a blob from the input image and then perform a forward
        # pass of the YOLO object detector, giving us our bounding boxes and
        # associated probabilities.
        blob = cv2.dnn.blobFromImage(img, 1 / 255.0, self.img_resize,
            swapRB=False, crop=False)
        self.yolo.setInput(blob)
        layer_output = self.yolo.forward(self.ln)

        # Initialize our lists of detected bounding boxes, confidences, and
        # class IDs, respectively.
        boxes = []
        confidences = []
        ids = []

        # Loop over each of the layer outputs.
        for output in layer_output:
            # Loop over each of the detections.
            for detection in output:
                # Extract the class ID and confidence (i.e., probability) of
                # the current object detection.
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
        
                # Filter out weak predictions by ensuring the detected
                # probability is greater than the minimum probability
                if confidence > score_thresh:
                    # Scale the bounding box coordinates back relative to the
                    # size of the image, keeping in mind that YOLO actually
                    # returns the center (x, y)-coordinates of the bounding
                    # box followed by the boxes' width and height
                    box = detection[0:4] * np.array([w, h, w, h])
                    (centerX, centerY, width, height) = box.astype("int")
        
                    # use the center (x, y)-coordinates to derive the top and
                    # and left corner of the bounding box
                    x = int(centerX - (width / 2))
                    y = int(centerY - (height / 2))
        
                    # update our list of bounding box coordinates, confidences,
                    # and class IDs
                    boxes.append([x, y, int(width), int(height)])
                    confidences.append(float(confidence))
                    ids.append(class_id)


        # Apply non-maxima suppression to suppress weak, overlapping bounding
        # boxes.
        idxs = cv2.dnn.NMSBoxes(boxes, confidences, score_thresh,
            nms_thresh)

        # Ensure at least one detection exists.
        if len(idxs) > 0:
            index = idxs.flatten()
            self.boxes = [boxes[i] for i in index]
            self.ids = [ids[i] for i in index]
        else:
            self.boxes = []
            self.ids = []
        # Update time stamp.
        self.time_stamp = time.time()
        

def debug():
    yolo = Yolov3(config='yolov3.cfg', weights='yolov3.weights')
    print(yolo.boxes, yolo.ids, yolo.time_stamp)
    yolo.predict(cv2.cvtColor(cv2.imread('dog.jpg'), cv2.COLOR_BGR2RGB))
    print(yolo.boxes, yolo.ids, yolo.time_stamp)
    print(yolo.boxes, yolo.ids, yolo.time_stamp)
    yolo.predict(cv2.cvtColor(cv2.imread('dog.jpg'), cv2.COLOR_BGR2RGB))
    print(yolo.boxes, yolo.ids, yolo.time_stamp)
