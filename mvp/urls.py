from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('about_us/', views.about_us, name='about_us'),
    path('contact_us/', views.contact_us, name='contact_us'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('workplace/', views.workplace, name='workplace'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('password_reset_combined/', views.password_reset_combined, name='password_reset_combined'),
    path('check_in/', views.check_in, name='check_in'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)