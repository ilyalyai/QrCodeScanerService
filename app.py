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

def PreprocessImage(image):
    # Конвертация в серый цвет
	#if len(image.shape) == 3:
		#gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	#else:
		#gray = image
    
    # Увеличение разрешения
	scale_factor = 2
	scaled = cv2.resize(image, None, fx=scale_factor, fy=scale_factor, 
						interpolation=cv2.INTER_CUBIC)
	# Мягкое подавление шума
	denoised = cv2.medianBlur(scaled, 3)

	# Улучшение контраста с помощью CLAHE
	#clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
	#enhanced = clahe.apply(denoised)
    
	return denoised

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
	#cv2.imwrite("0.jpg", image)

	#обработка всякими фильтрами
	image1 = PreprocessImage(image)

	#если не нашли - обрежем пополам и снова поищем
	#решил проверят нефильтрованное изображение - фильтр код ломает
	height, width = image.shape[:2]
	croppedImage0 = image[height // 2:, :]
	croppedImage1 = croppedImage0[:, width // 2:]
	
	#на 4 части
	height, width = croppedImage1.shape[:2]
	croppedImage2 = croppedImage1[height // 2:, :]
	croppedImage3 = croppedImage2[:, width // 2:]
	
	#на 8 частей
	height, width = croppedImage3.shape[:2]
	croppedImage4 = croppedImage3[height // 2:, :]
	croppedImage5 = croppedImage4[:, width // 2:]
	
	# Initialize QReader
	detector = QReader()
	#декодер OpenCV. Быстрее, но не видит почти ничего
	qcd = cv2.QRCodeDetector()

	images = [image, image1, croppedImage0, croppedImage1, croppedImage2, croppedImage3, croppedImage3, croppedImage4, croppedImage5]

	#дадим шанс opencv
	for imageToDecode in images:
		# внутри уже есть проверка на пустую строку и None, так что проверим, что вернули хоть что-то
		result = CheckImage(imageToDecode, qcd)
		if result is not None:
			return result
		
	#opencv шанс не оправдал. QrCoder, твой выход
	for imageToDecode in images:
		result = CheckImage(imageToDecode, detector)
		if result is not None:
			return result
	
	return Response(
		response="QR codes not detected.",
		status=HTTPStatus.OK,
		content_type='application/json'
	)

def CheckImage(image, qcd):
	try:
		decoded_text = qcd.detect_and_decode(image=image, is_bgr = True)
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