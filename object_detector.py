# USAGE
# python pi_object_detection.py --prototxt MobileNetSSD_deploy.prototxt.txt --model MobileNetSSD_deploy.caffemodel

# import the necessary packages
from imutils.video import VideoStream
from imutils.video import FPS
from picamera import PiCamera
from multiprocessing import Process
from multiprocessing import Queue
import numpy as np
import argparse
import imutils
import time
import cv2
import datetime


MIN_CONFIDENCE=0.7

# initialize the list of class labels MobileNet SSD was trained to
# detect, then generate a set of bounding box colors for each class
CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
        "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
        "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
        "sofa", "train", "tvmonitor"]
COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))

# load our serialized model from disk
print("[INFO] loading model...")
net = cv2.dnn.readNetFromCaffe("MobileNetSSD_deploy.prototxt.txt", "MobileNetSSD_deploy.caffemodel")

print("[INFO] starting video stream...")
vs = VideoStream(src=0, resolution=(1024,768)).start()
#vs = VideoStream(usePiCamera=True).start()
#camera = PiCamera()
#camera.resolution = (1024, 768)


# initialize the input queue (frames), output queue (detections),
# and the list of actual detections returned by the child process
inputQueue       = Queue(maxsize=1)
outputQueue      = Queue(maxsize=1)
detections       = None
show_high_gui    = False
write_video_file = False

if show_high_gui:
    cv2.namedWindow("Security-Cam")
if write_video_file:
    video_output = cv2.VideoWriter('security-cam-out.avi',cv2.VideoWriter_fourcc('M','J','P','G'), 10, (1024,768))

def classify_frame_process(net, inputQueue, outputQueue):
  while True:
    if not inputQueue.empty():
      # grab the frame from the input queue, resize it, and
      # construct a blob from it
      frame = inputQueue.get()
      detections = classify_frame(net, frame)
      outputQueue.put(detections)

def classify_frame(net, frame):
    # check to see if there is a frame in our input queue
      frame = cv2.resize(frame, (300, 300))
      blob = cv2.dnn.blobFromImage(frame, 0.007843, (300, 300), 127.5)

      # set the blob as input to our deep learning object
      # detector and obtain the detections
      net.setInput(blob)
      detections = net.forward()
      return detections

def concurrentcy():

  # construct a child process *indepedent* from our main process of
  # execution
  print("[INFO] starting process...")
  p = Process(target=classify_frame, args=(net, inputQueue, outputQueue,))
  p.daemon = True
  p.start()

def detect():
  frame = vs.read()
  frame = imutils.resize(frame, width=1024)
  (fH, fW) = frame.shape[:2]

  # if the input queue *is* empty, give the current frame to
  # classify
  #if inputQueue.empty():
  #  inputQueue.put(frame)

  # if the output queue *is not* empty, grab the detections
  #if not outputQueue.empty():
  #  detections = outputQueue.get()
  detections = classify_frame(net, frame)
  detected_objects = []

  # check to see if our detectios are not None (and if so, we'll
  # draw the detections on the frame)
  if detections is not None:
    # loop over the detections

    # print("items found ", detections.shape[2])
    for i in np.arange(0, detections.shape[2]):
      # extract the confidence (i.e., probability) associated
      # with the prediction
      confidence = detections[0, 0, i, 2]

      # filter out weak detections by ensuring the `confidence`
      # is greater than the minimum confidence
      # print(confidence)
      if confidence < MIN_CONFIDENCE:
        continue
      else:
        # otherwise, extract the index of the class label from
        # the `detections`, then compute the (x, y)-coordinates
        # of the bounding box for the object
        idx = int(detections[0, 0, i, 1])
        #print("we are confident, that we detected: ", CLASSES[idx])

        dims = np.array([fW, fH, fW, fH])
        box = detections[0, 0, i, 3:7] * dims
        (startX, startY, endX, endY) = box.astype("int")
        # print(box.astype("int"))

        # draw the prediction on the frame
        label = CLASSES[idx]
        label_string= "{}: {:.2f}%".format(label, confidence * 100)
        cv2.rectangle(frame, (startX, startY), (endX, endY), COLORS[idx], 2)
        y = startY - 15 if startY - 15 > 15 else startY + 15
        cv2.putText(frame, label_string, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS[idx], 2)
        # just for debugging
        now = datetime.datetime.now()
        cv2.putText(frame, now.strftime("%Y-%m-%d %H:%M"), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS[0], 2)

        center = (startX + endX ) / 2
        detected_objects.append((label, center))

  else:
      print("nothing detected")
  ## show the output frame
  if show_high_gui:
      cv2.imshow("Security-Cam", frame)
      cv2.waitKey(10)
      #cv2.destroyAllWindows()
  if write_video_file:
      video_output.write(frame)
  cv2.imwrite("security-cam.jpg", frame)
  return detected_objects
