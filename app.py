from flask import Flask, Response
from flask import request
from http import HTTPStatus
import cv2
import numpy as np

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
	
	image = cv2.imdecode(np.frombuffer(img, dtype=np.uint8), cv2.IMREAD_COLOR)
	if image is None:
		return Response(
			response="Failed to decode image.",
			status=HTTPStatus.BAD_REQUEST,
			content_type='text/plain'
		)
	
	try:
		qcd = cv2.QRCodeDetector()
		retval, decoded_info, points, straight_qrcode = qcd.detectAndDecodeMulti(image)
	except Exception as e:
		return Response(
            response=f"Error detecting QR codes: {str(e)}",
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
            content_type='text/plain'
        )
	
	if not retval:
		return Response(
			response="QR codes not detected.",
			status=HTTPStatus.OK,
			content_type='application/json'
		)
	else:
		return Response(
			response=' '.join(decoded_info),
			status=HTTPStatus.OK,
			content_type='application/json'
		)


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8003)
