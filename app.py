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
	image = cv2.imdecode(np.frombuffer(img, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
	if image is None:
		return Response(
			response="Failed to decode image.",
			status=HTTPStatus.BAD_REQUEST,
			content_type='text/plain'
		)
	# Initialize QReader
	detector = QReader()
	# Detect the QR bbox
	result = CheckImage(image, detector)
	if result is not None:
		return result

	#если не нашли - обрежем пополам и снова поищем
	#решил проверят нефильтрованное изображение - фильтр код ломает
	height, width = image.shape[:2]
	croppedImage = image[height // 2:, :]
	result = CheckImage(croppedImage, detector)
	if result is not None:
		return result
	
	#и снова пополам
	croppedImage = croppedImage[:, width // 2:]
	result = CheckImage(croppedImage, detector)
	if result is not None:
		return result
	
	return Response(
		response="QR codes not detected.",
		status=HTTPStatus.OK,
		content_type='application/json'
	)

def CheckImage(image, qcd):
	try:
		decoded_text = qcd.detect_and_decode(image=image)
		if decoded_text is not None:
			result = ''.join(str(x) for x in decoded_text)
			if result != "None" and result != "":
				return Response(
					response=' '.join(str(x) for x in decoded_text),
					status=HTTPStatus.OK,
					content_type='application/json'
				)
		return None
	except Exception as e:
		return Response(
            response=f"Error detecting QR codes: {str(e)}",
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
            content_type='text/plain'
        )

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8003)