from django.urls import path
from . import views

urlpatterns = [
    path('', views.homePage, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('task/update/<int:pk>/', views.task_update, name='update_task'),
    path('task/delete/<int:task_id>/', views.delete_task, name='delete_task'),  # Delete task
    path('toggle-task/<int:task_id>/', views.toggle_task, name='toggle_task'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('features/', views.features, name='features'),
    path('resources/', views.resources, name='resources'),
    path('aboutus/', views.aboutus, name='aboutus'),
]
