import io
import mysql.connector
import torch
from flask import Flask, request, jsonify
import random
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from yolov5 import detect
import pandas as pd

weights = "best.pt"
source = "path/to/images"
data = "coco128.yaml"
imgsz = (640, 640)
conf_thres = 0.25
iou_thres = 0.45
max_det = 1000
device = ""
view_img = False
save_txt = False
save_conf = False
save_crop = False
nosave = False
classes = None
agnostic_nms = False
augment = False
visualize = False
update = False
project = "D://work//elderwatchAI//results"
name = "exp"
exist_ok = False
line_thickness = 3
hide_labels = False
hide_conf = False
half = False
dnn = False
vid_stride = 1

app = Flask(__name__)

# Load the YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'custom', path='./best.pt')

# Connect to MySQL database
mydb = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="Develop@2021",
    database="elderdb"
)
mycursor = mydb.cursor()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

executor = ThreadPoolExecutor()

@app.route('/hello', methods=['GET'])
def hello():
    return "Hello World"


@app.route('/detect', methods=['POST'])
def detect_objects():
    # Check if request has an id field
    if 'id' not in request.form:
        logger.error("Missing id field")
        return jsonify(error="Missing id field"), 400

    # Get the id from the form data
    id = request.form['id']

    storagePath = request.form['storagePath']
    rawImage = request.form.get('image_url', '')
    # Get the image URL from the request
    image_url = "http://localhost:8443" + rawImage
    if not image_url:
        logger.error("Missing image URL field")
        return jsonify(error="Missing image URL field"), 400

    rand_num = random.randint(1, 3)

    # Perform object detection asynchronously
    executor.submit(do_object_detection, id, image_url, rand_num,storagePath, rawImage)

    logger.info("Object detection process started in the background.")
    print()
    print()
    return 'Object detection process started.'

def do_object_detection(id, image_url, rand_num,storagePath, rawImage):
    # Fetch the image from the URL
    # response = requests.get(image_url)
    # if response.status_code != 200:
    #     logger.error("Failed to fetch image")
    #     return

    # Read the image content and convert to bytes
    # image_bytes = io.BytesIO(response.content)

    # Detect objects in the image
    #loading_bar(100, prefix='Progress:', suffix='Complete', length=30, fill='█', empty='─')
    results = model(image_url)

    fallDetection = 0
    
    try:
        # Convert results to a Pandas DataFrame
        df = results.pandas().xyxy[0]

        # Get the number of detected objects
        fallDetection = df.shape[0]


    except Exception as e:
        print("Error:", str(e))


    # Iterate over the detected objects and persist to MySQL database
    for result in results.xyxy:

        if fallDetection>0:
            storagePath = storagePath.replace("/","//")
            rawImageSlice = rawImage.split("/")
            imageNoExt = rawImageSlice[3].split(".")
            imagePath = "/storage/results/" + imageNoExt[0] +".jpg"


    logger.info("Object detection complete.")

def runData(imageUrl):
    detect.run(weights=weights, source=imageUrl, data=data, imgsz=imgsz, conf_thres=conf_thres, iou_thres=iou_thres,
    max_det=max_det, device=device, view_img=view_img, save_txt=save_txt, save_conf=save_conf, save_crop=save_crop,
    nosave=nosave, classes=classes, agnostic_nms=agnostic_nms, augment=augment, visualize=visualize, update=update,
    project=project, name=name, exist_ok=exist_ok, line_thickness=line_thickness, hide_labels=hide_labels,
    hide_conf=hide_conf, half=half, dnn=dnn, vid_stride=vid_stride)


if __name__ == '__main__':
    app.run()
