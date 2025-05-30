from flask import Flask, Response
from flask import request
from http import HTTPStatus
import numpy as np
from qreader import QReader
import cv2

app = Flask(__name__)

@app.route('/')
def hello():
	return "Hello World!"

@app.route('/scan_for_qr_code', methods=['POST'])
def scan_for_qr_code():
	img = request.get_data()
	if img is None:
		return Response(
			response="Empty imput image!",
			status=HTTPStatus.BAD_REQUEST,
			content_type='text/plain'
		)
	image = cv2.imdecode(np.frombuffer(img, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
	if image is None:
		return Response(
			response="Failed to decode image.",
			status=HTTPStatus.BAD_REQUEST,
			content_type='text/plain'
		)
	# Initialize QReader
	detector = QReader()
	# Detect the QR bbox
	decoded_text = detector.detect_and_decode(image=image)
	if decoded_text:
		return Response(
			response=decoded_text,
			status=HTTPStatus.OK,
			content_type='application/json'
		)
	else:
		return Response(
		response="QR codes not detected.",
		status=HTTPStatus.OK,
		content_type='application/json'
	)

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8003)