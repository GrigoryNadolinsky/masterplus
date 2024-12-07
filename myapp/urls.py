# myapp/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('new/', views.request_create, name='request_create'),
    path('edit/<int:pk>/', views.request_update, name='request_update'),
    path('delete/<int:pk>/', views.request_delete, name='request_delete'),
    path('take/<int:pk>/', views.request_take, name='request_take'),
    path('assign/<int:pk>/', views.request_assign, name='request_assign'),  # Добавленный URL
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('ajax/load-repair-types/', views.ajax_load_repair_types, name='ajax_load_repair_types'),
    path('ajax/load-repair-details/', views.ajax_load_repair_details, name='ajax_load_repair_details'),
    path('assign/<int:pk>/', views.request_assign, name='request_assign'),
    path('profile/change_password/', views.change_password, name='change_password'),
    path('request/<int:pk>/view/', views.request_view, name='request_view'),
    path('request/<int:pk>/edit/', views.request_update, name='request_update'),
]
