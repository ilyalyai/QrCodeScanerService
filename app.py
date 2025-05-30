from flask import Flask, Response
from flask import request
from http import HTTPStatus
import numpy as np
from qreader import QReader

import sys
import importlib

# 1. Удаляем `cv2` из кеша модулей (если он уже загружен)
sys.modules.pop("cv2", None)  

# 2. Принудительно загружаем headless-версию
try:
    # Пытаемся импортировать headless
    cv2 = importlib.import_module("cv2")
    print("✅ Используется OpenCV Headless")
except ImportError:
    # Если headless нет, пробуем обычную версию (но с предупреждением)
    from cv2 import cv2  
    print("⚠️ Headless не найден, используется обычная OpenCV")

# 3. Проверяем, что загружена headless-версия
is_headless = "headless" in cv2.getBuildInformation().lower()
print(f"Headless mode: {is_headless}")

app = Flask(__name__)

'''
def CheckImage(image, qcd):
	try:
		#retval, decoded_info, points, straight_qrcode = qcd.detectAndDecodeMulti(image)
		data, points, _ = qcd.detectAndDecode(image)
	except Exception as e:
		return Response(
            response=f"Error detecting QR codes: {str(e)}",
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
            content_type='text/plain'
        )
	if points is not None and data:
	#if retval:
		return Response(
			response=data,
			#response=' '.join(decoded_info),
			status=HTTPStatus.OK,
			content_type='application/json'
		)
	else:
		return None	
#я люблю тебя дипсик
def PreprocessImage(image):
    # Конвертация в серый цвет
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # Увеличение разрешения
    scale_factor = 2.0
    scaled = cv2.resize(gray, None, fx=scale_factor, fy=scale_factor, 
                        interpolation=cv2.INTER_CUBIC)
    
    # Мягкое подавление шума
    denoised = cv2.medianBlur(scaled, 3)
    
    # Улучшение контраста с помощью CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)
    
    return enhanced
'''
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
'''
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
	updatedImage = PreprocessImage(image)
	#image = cv2.resize(image, None, fx=2.0, fy=2.0)  # Увеличение размера
	#image = cv2.imdecode(np.frombuffer(img, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
	qcd = cv2.QRCodeDetector()
	#Сначала поищем код без фильтрации
	cv2.imwrite("0.jpg", updatedImage)
	result = CheckImage(updatedImage, qcd)
	if result is not None:
		return result
	for scale in [1.5, 2.0, 2.5, 3.0]:
		scaled = cv2.resize(image, None, fx=scale, fy=scale, 
							interpolation=cv2.INTER_CUBIC)
		cv2.imwrite(str(scale) + "scaled.jpg", scaled)
		result = CheckImage(scaled, qcd)
		if result is not None:
			return result
	for thresh in range(50, 200, 30):
		_, binary = cv2.threshold(image, thresh, 255, cv2.THRESH_BINARY)
		cv2.imwrite(str(thresh) + "binary.jpg", binary)
		result = CheckImage(binary, qcd)
		if result is not None:
			return result
    
     # Стратегия 4: Адаптивная бинаризация
	adaptive = cv2.adaptiveThreshold(
        image, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
	cv2.imwrite("1.jpg", adaptive)
	result = CheckImage(adaptive, qcd)
	if result is not None:
		return result
    
    # Стратегия 5: Морфологические операции
	kernel = np.ones((3, 3), np.uint8)
	morphed = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
	cv2.imwrite("2.jpg", morphed)
	result = CheckImage(morphed, qcd)
	if result is not None:
		return result
	
	#scaled = cv2.resize(image, None, fx=scale, fy=scale, 
	#						interpolation=cv2.INTER_CUBIC)
	#если не нашли - обрежем пополам и снова поищем
	#решил проверят нефильтрованное изображение - фильтр код ломает
	height, width = image.shape[:2]
	croppedImage = image[height // 2:, :]
	cv2.imwrite("3.jpg", croppedImage)
	result = CheckImage(croppedImage, qcd)
	if result is not None:
		return result
	
	#и снова пополам
	croppedImage = croppedImage[:, width // 2:]
	cv2.imwrite("4.jpg", croppedImage)
	result = CheckImage(croppedImage, qcd)
	if result is not None:
		return result
	
	croppedImage = croppedImage[height // 2:, :]
	cv2.imwrite("5.jpg", croppedImage)
	result = CheckImage(croppedImage, qcd)
	if result is not None:
		return result
	
	#и снова пополам
	croppedImage = croppedImage[:, width // 2:]
	cv2.imwrite("6.jpg", croppedImage)
	result = CheckImage(croppedImage, qcd)
	if result is not None:
		return result
	
	croppedImage = croppedImage[height // 2:, :]
	cv2.imwrite("7.jpg", croppedImage)
	result = CheckImage(croppedImage, qcd)
	if result is not None:
		return result
	
	#и снова пополам
	croppedImage = croppedImage[:, width // 2:]
	cv2.imwrite("8.jpg", croppedImage)
	result = CheckImage(croppedImage, qcd)
	if result is not None:
		return result
	
	return Response(
		response="QR codes not detected.",
		status=HTTPStatus.OK,
		content_type='application/json'
	)
'''

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8003)