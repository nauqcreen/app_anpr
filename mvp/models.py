from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    hometown = models.CharField(max_length=255, null=True, blank=True)
    job_position = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.user.username

class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    feedback = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f'Feedback from {self.user.username} on {self.timestamp}'

class AdminReply(models.Model):
    feedback = models.OneToOneField(Feedback, on_delete=models.CASCADE, related_name='reply')
    reply = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply to {self.feedback.user.username} on {self.timestamp}"

class CheckInOut(models.Model):
    VEHICLE_TYPES = [
        ('Car', 'Car'),
        ('Motorbike', 'Motorbike'),
        ('Bicycle', 'Bicycle'),
    ]
    plate_number = models.CharField(max_length=20)
    vehicle_type = models.CharField(max_length=10, choices=VEHICLE_TYPES, default='Car')
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.plate_number

class ParkingFee(models.Model):
    vehicle_type = models.CharField(max_length=20, choices=[('Car', 'Car'), ('Motorbike', 'Motorbike'), ('Bicycle', 'Bicycle')])
    fee_per_hour = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f'{self.vehicle_type} - {self.fee_per_hour or "N/A"}/hour'
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.vehicle_type == 'Car' and (self.fee_per_hour is None or self.fee_per_hour == 0):
            raise ValidationError('Fee per hour for Car cannot be null or zero.')

class AdminReply(models.Model):
    feedback = models.OneToOneField(Feedback, on_delete=models.CASCADE, related_name='reply')
    reply = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply to {self.feedback.user.username} on {self.timestamp}"

class CheckIn(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    date = models.DateField()
    checked_in = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.user.username} - {self.date}'