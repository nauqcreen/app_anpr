from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from .models import Profile, Feedback, ParkingFee, CheckInOut, CheckIn
from django.utils import timezone
from .autoplate import preprocess_image, deskew_plate, text, detect_objects, check_in, check_out, calculate_parking_fee
import cv2
import numpy as np
import os
from PIL import Image
from io import BytesIO
from .forms import CheckInOutForm, ProfileUpdateForm


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
        
        messages.success(request, f'Chúc mừng {username} đăng kí tài khoản thành viên thành công!')
        return redirect('login')
    return render(request, 'register.html')

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request, f'Chúc mừng {username} đã đăng nhập tài khoản thành công!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng.')
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
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('dashboard')
    else:
        form = ProfileUpdateForm(instance=profile)

    return render(request, 'dashboard.html', {'profile': profile, 'form': form})

def about_us(request):
    return render(request, 'about_us.html')

@login_required
def check_in(request):
    if request.method == 'POST':
        start_time = request.POST['start_time']
        end_time = request.POST['end_time']
        date = timezone.now().date()

        check_in = CheckIn(
            user=request.user,
            start_time=start_time,
            end_time=end_time,
            date=date
        )
        check_in.save()
        messages.success(request, "Check-in successful.")
        return redirect('dashboard')

    return render(request, 'dashboard.html')

@login_required
def contact_us(request):
    if request.method == 'POST':
        feedback = request.POST['feedback']
        Feedback.objects.create(
            user=request.user,
            feedback=feedback,
            timestamp=timezone.now()
        )
        messages.success(request, 'Feedback của bạn đã được gửi đi đến admin thành công!')
        return redirect('contact_us')
    return render(request, 'contact_us.html', {'user': request.user})

@login_required
def workplace(request):
    if request.user.is_superuser:
        return redirect('/admin/')  # Chuyển hướng đến trang quản lý admin nếu người dùng là admin

    vehicle_types = ['Car', 'Motorbike', 'Bicycle']
    check_in_record = None
    parking_fee = None
    records = CheckInOut.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'process_image':
            confidence_threshold = float(request.POST.get('confidence_threshold', 0.5))
            model_type = request.POST.get('model_type', 'v8')
            vehicle_type = request.POST.get('vehicle_type', 'Car')
            image = request.FILES.get('image')
            
            if image:
                plate_number, processed_img = recognize_plate(image, model_type, confidence_threshold)
                if plate_number:
                    check_in_records = CheckInOut.objects.filter(plate_number=plate_number, check_out_time__isnull=True)
                    if not check_in_records.exists():
                        check_in_record = CheckInOut.objects.create(
                            plate_number=plate_number,
                            vehicle_type=vehicle_type,
                            check_in_time=timezone.now(),
                            image=image
                        )
                        messages.success(request, f'Check-in successful! Plate number: {plate_number}')
                    else:
                        check_in_record = check_in_records.first()
                        check_in_record.check_out_time = timezone.now()
                        check_in_record.image = image
                        check_in_record.save()
                        parking_fee = calculate_parking_fee(plate_number)
                        messages.success(request, f'Check-out successful! Plate number: {plate_number}. Parking fee: {parking_fee} VNĐ')
            return redirect('workplace')

        elif action == 'add':
            form = CheckInOutForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Record added successfully!')
                return redirect('workplace')
        elif action == 'edit':
            record_id = request.POST.get('record_id')
            record = get_object_or_404(CheckInOut, id=record_id)
            form = CheckInOutForm(request.POST, instance=record)
            if form.is_valid():
                form.save()
                messages.success(request, 'Record updated successfully!')
                return redirect('workplace')
        elif action == 'delete':
            record_id = request.POST.get('record_id')
            record = get_object_or_404(CheckInOut, id=record_id)
            record.delete()
            messages.success(request, 'Record deleted successfully!')
            return redirect('workplace')

    add_form = CheckInOutForm()
    return render(request, 'workplace.html', {'vehicle_types': vehicle_types, 'records': records, 'check_in_record': check_in_record, 'parking_fee': parking_fee, 'add_form': add_form})

def recognize_plate(image, model_type, confidence_threshold):
    img = Image.open(image)
    img = img.convert('RGB')  # Ensure image is in RGB format
    img = np.array(img)

    if img.ndim == 3 and img.shape[2] == 3:
        img = img[..., ::-1]  # Convert RGB to BGR if needed

    img = preprocess_image(img)

    plates, img = detect_objects(img, confidence_threshold, model_type)

    if plates:
        plate_number = text(plates[0])  # Assuming one plate per image for simplicity
        return plate_number, img
    return None, img


def calculate_fee(check_in_record):
    check_in_time = check_in_record.check_in_time
    check_out_time = check_in_record.check_out_time
    duration = (check_out_time - check_in_time).total_seconds() / 3600  # duration in hours
    vehicle_type = check_in_record.vehicle_type
    parking_fee = ParkingFee.objects.get(vehicle_type=vehicle_type)
    if parking_fee.fee_per_hour is None:
        return 0
    fee = duration * parking_fee.fee_per_hour
    return round(fee, 2)