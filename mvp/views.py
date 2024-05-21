from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from .models import Profile, Feedback, ParkingFee, CheckInOut, InOut
from django.utils import timezone
from .autoplate import preprocess_image, deskew_plate, text, check_in, check_out, calculate_parking_fee
import cv2
import numpy as np
import os
from PIL import Image
from io import BytesIO
from .forms import CheckInOutForm, ProfileUpdateForm
import json
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.files.storage import FileSystemStorage
import math
import easyocr
from datetime import datetime
from deskew import determine_skew
from django.utils import timezone


def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        birth_date = request.POST['birth_date']
        email = request.POST['email']
        gender = request.POST['gender']
        address = request.POST['address']
        hometown = request.POST['hometown']
        job_position = request.POST['job_position']
        username = request.POST['username']
        password = request.POST['password']
        
        user = User.objects.create_user(username=username, password=password, email=email)
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        
        user.profile.birth_date = birth_date
        user.profile.gender = gender
        user.profile.address = address
        user.profile.hometown = hometown
        user.profile.job_position = job_position
        user.profile.save()
        
        messages.success(request, f'{username} sign up your new account successfully !, the falcuty management will approve {username} profile if you are an employee !')
        return redirect('login')
    return render(request, 'register.html')

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request, f'Congratulate {username} sign in successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Neither username nor password is not correct ! Recheck & enter again !')
    return render(request, 'login.html')

def password_reset_combined(request):
    if request.method == 'POST':
        email = request.POST['email']
        new_password1 = request.POST['new_password1']
        new_password2 = request.POST['new_password2']

        if new_password1 != new_password2:
            messages.error(request, "Passwords do not match.")
            return redirect('password_reset_combined')

        try:
            user = User.objects.get(email=email)
            user.password = make_password(new_password1)
            user.save()
            messages.success(request, "Password reset successful.")
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, "User with this email does not exist.")
            return redirect('password_reset_combined')

    return render(request, 'password_reset_combined.html')

@login_required
def dashboard(request):
    profile = request.user.profile
    feedbacks = Feedback.objects.filter(user=request.user).order_by('-timestamp')
    unread_feedbacks_count = feedbacks.filter(read=False).count()

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('dashboard')
    else:
        form = ProfileUpdateForm(instance=profile)

    return render(request, 'dashboard.html', {
        'profile': profile,
        'form': form,
        'feedbacks': feedbacks,
        'unread_feedbacks_count': unread_feedbacks_count
    })

@login_required
def send_reply(request, feedback_id):
    feedback = get_object_or_404(Feedback, id=feedback_id)
    if request.method == 'POST':
        reply_text = request.POST['reply']
        AdminReply.objects.create(feedback=feedback, reply=reply_text)
        feedback.read = True
        feedback.save()
        messages.success(request, 'Reply sent successfully.')
        return redirect('dashboard')
    return render(request, 'dashboard')

@login_required
@csrf_exempt
def mark_all_read(request):
    if request.method == 'POST':
        feedbacks = Feedback.objects.filter(user=request.user, read=False)
        feedbacks.update(read=True)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

def about_us(request):
    return render(request, 'about_us.html')

@method_decorator(csrf_exempt, name='dispatch')
class CheckInOutView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            check_type = data.get('check_type')
            user_id = data.get('user_id')
            date = data.get('date')
            start_time = data.get('start_time')
            end_time = data.get('end_time')

            user = User.objects.get(id=user_id)

            if check_type == 'check-in':
                InOut.objects.create(user=user, check_type=check_type, date=date, start_time=start_time, end_time=end_time)
            elif check_type == 'check-out':
                InOut.objects.create(user=user, check_type=check_type, date=date, start_time=start_time)

            response = {
                'status': 'success',
                'message': f'{check_type.capitalize()} information received for {user.username} on {date} at {start_time}.'
            }
            return JsonResponse(response)
        except User.DoesNotExist:
            response = {
                'status': 'error',
                'message': 'User does not exist.'
            }
            return JsonResponse(response, status=404)
        except Exception as e:
            response = {
                'status': 'error',
                'message': str(e)
            }
            return JsonResponse(response, status=400)

@login_required
def contact_us(request):
    if request.method == 'POST':
        feedback = request.POST['feedback']
        Feedback.objects.create(
            user=request.user,
            feedback=feedback,
            timestamp=timezone.now()
        )
        messages.success(request, 'Your Feedback is sent to admin !')
        return redirect('contact_us')
    return render(request, 'contact_us.html', {'user': request.user})

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
        # Ensure the image has 3 channels
        if len(image.shape) == 2 or image.shape[2] == 1:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        
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
        record.check_in_time = timezone.now()  # Use timezone-aware datetime
        record.vehicle_type = vehicle_type
        record.image = image_url
        record.save()
    else:
        return record

# Calculate parking fee function
def calculate_parking_fee(record):
    if record and record.check_out_time:
        check_in_time = record.check_in_time
        check_out_time = record.check_out_time
        parking_duration = (check_out_time - check_in_time).total_seconds() / 3600  # Convert to hours
        fee_per_hour = 100000  # Example fee
        return parking_duration * fee_per_hour
    return 0

# Check-out function
def check_out(plate_number):
    try:
        record = CheckInOut.objects.get(plate_number=plate_number, check_out_time__isnull=True)
        record.check_out_time = timezone.now()  # Use timezone-aware datetime
        record.parking_fee = calculate_parking_fee(record)  # Save parking fee
        record.save()
        return record
    except CheckInOut.DoesNotExist:
        return None

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

            # Read the image file correctly
            image_file.open()  # Reopen the file to reset the read pointer
            image_data = np.frombuffer(image_file.read(), np.uint8)
            if image_data.size != 0:
                image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
                processed_image = preprocess_image(image)
                deskewed_image = deskew_plate(processed_image)
                plate_text = text(deskewed_image)
                
                if plate_text.strip():
                    record = check_in(plate_text, vehicle_type, uploaded_file_url)
                    if not record:
                        record = check_out(plate_text)
                    
                    parking_fee = calculate_parking_fee(record)

                    return render(request, 'workplace.html', {
                        'check_in_record': record,
                        'parking_fee': parking_fee
                    })
                else:
                    print("Error: The plate text is empty.")
                    return render(request, 'workplace.html', {'error': 'The plate text is empty or could not be recognized.'})
            else:
                print("Error: The image buffer is empty.")
                return render(request, 'workplace.html', {'error': 'The uploaded image is empty or corrupted.'})

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

