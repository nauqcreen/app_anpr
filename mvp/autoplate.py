import cv2
import math
import easyocr
import numpy as np
from datetime import datetime
from deskew import determine_skew
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from .models import CheckInOut

# Set the language for OCR
reader = easyocr.Reader(['en'])

# Image pre-processing function
def preprocess_image(img):
    img = cv2.resize(img, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.fastNlMeansDenoising(img, None, 30, 7, 21)
    img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)
    smooth = cv2.GaussianBlur(img, (1, 1), 0)
    return smooth

# Image deskewing function
def deskew_plate(image):
    try:
        grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        angle = determine_skew(grayscale)
        old_width, old_height = image.shape[:2]
        angle_radian = math.radians(angle)
        width = abs(np.sin(angle_radian) * old_height) + abs(np.cos(angle_radian) * old_width)
        height = abs(np.sin(angle_radian) * old_width) + abs(np.cos(angle_radian) * old_height)
        image_center = tuple(np.array(image.shape[1::-1]) / 2)
        rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
        rot_mat[1, 2] += (width - old_width) / 2
        rot_mat[0, 2] += (height - old_height) / 2
        return cv2.warpAffine(image, rot_mat, (int(round(height)), int(round(width))), borderValue=(0, 0, 0))
    except Exception as e:
        print(f"Error deskewing plate: {e}")
        return image

# Text extraction function
def text(img):
    try:
        plate_text = ''
        for ele in reader.readtext(img, allowlist=".-0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            plate_text += str(ele[1])
        return plate_text
    except:
        return ' '

# Check-in function
def check_in(plate_number, vehicle_type, image_url):
    record, created = CheckInOut.objects.get_or_create(plate_number=plate_number, check_out_time__isnull=True)
    if created:
        record.check_in_time = datetime.now()
        record.vehicle_type = vehicle_type
        record.image = image_url
        record.save()

# Check-out function
def check_out(plate_number):
    try:
        record = CheckInOut.objects.get(plate_number=plate_number, check_out_time__isnull=True)
        record.check_out_time = datetime.now()
        record.save()
    except CheckInOut.DoesNotExist:
        print(f"No check-in record found for plate number: {plate_number}")

# Calculate parking fee function
def calculate_parking_fee(plate_number):
    try:
        record = CheckInOut.objects.get(plate_number=plate_number, check_out_time__isnull=False)
        check_in_time = record.check_in_time
        check_out_time = record.check_out_time
        parking_duration = (check_out_time - check_in_time).total_seconds() / 3600  # Convert to hours
        fee_per_hour = 15000  # Example fee
        return parking_duration * fee_per_hour
    except CheckInOut.DoesNotExist:
        return 0

# Main view function
def workplace(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'process_image':
            confidence_threshold = float(request.POST.get('confidence_threshold'))
            model_type = request.POST.get('model_type')
            vehicle_type = request.POST.get('vehicle_type')

            image_file = request.FILES['image']
            fs = FileSystemStorage()
            filename = fs.save(image_file.name, image_file)
            uploaded_file_url = fs.url(filename)

            image = cv2.imdecode(np.frombuffer(image_file.read(), np.uint8), cv2.IMREAD_COLOR)
            processed_image = preprocess_image(image)
            deskewed_image = deskew_plate(processed_image)
            plate_text = text(deskewed_image)
            
            check_in(plate_text, vehicle_type, uploaded_file_url)
            parking_fee = calculate_parking_fee(plate_text)

            check_in_record = CheckInOut.objects.get(plate_number=plate_text, check_out_time__isnull=True)
            return render(request, 'workplace.html', {
                'check_in_record': check_in_record,
                'parking_fee': parking_fee
            })

        elif action == 'add':
            # Handle adding new records here
            pass

        elif action == 'edit':
            # Handle editing records here
            pass

        elif action == 'delete':
            # Handle deleting records here
            pass

        elif action == 'update_fee':
            # Handle updating fee here
            pass

    records = CheckInOut.objects.all()
    return render(request, 'workplace.html', {'records': records})
