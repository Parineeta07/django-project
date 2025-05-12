from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .forms import TaskForm
from .models import Task, MoodEntry
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test, login_required
from django.db.models import Count
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import requests
import os
import logging
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json


# Setup logging
logger = logging.getLogger(__name__)

# Fetch Flask API URL from environment variables (use default for development)
FLASK_API_URL = getattr(settings, 'FLASK_API_URL', 'http://127.0.0.1:5000/api/analyze')

def homePage(request):
    return render(request, 'home.html')

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        selected_role = request.POST.get('role')

        # Authenticate user
        user = authenticate(request, username=username, password=password)

        if user:
            if (selected_role == 'admin' and user.is_superuser) or (selected_role == 'user' and not user.is_superuser):
                # Log the user in
                login(request, user)

                # Redirect based on role
                return redirect('admin_dashboard' if user.is_superuser else 'dashboard')
            else:
                messages.error(request, "Invalid credentials: Role mismatch")
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'login.html')


def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        cpassword = request.POST.get('cpassword')

        if password != cpassword:
            messages.error(request, 'Passwords do not match')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already used')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, 'Registration successful! You can now login.')
            return redirect('login')

    return render(request, 'signup.html')


def analyze_mood(username, task_message):
    url = 'http://127.0.0.1:5000/api/analyze'  # Your Flask API URL
    response = requests.post(url, json={'message': task_message, 'name': username})

    if response.status_code == 200:
        data = response.json()
        mood_data = data.get('mood', 'neutral')
        error_message = data.get('error_message', '')
        return mood_data, error_message
    else:
        return 'neutral', 'Error in mood analysis'


@csrf_exempt
def dashboard_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated."}, status=401)

    user = request.user  # Get the current authenticated user
    tasks = Task.objects.filter(user=user)  # Get tasks associated with the current user
    task_count = tasks.count()

    # Calculate task progress
    completed_tasks = tasks.filter(status='completed').count() if task_count > 0 else 0
    progress_percentage = (completed_tasks / task_count) * 100 if task_count > 0 else 0

    # Get the latest task description for mood analysis
    latest_task = tasks.order_by('-created_at').first()
    task_message = latest_task.description.strip() if latest_task and latest_task.description else "Feeling okay."

    # Analyze the mood based on the task message (initial mood analysis for the GET request)
    mood_data, error_message = analyze_mood(user.username, task_message)

    # If it's a POST request (e.g., from Postman)
    if request.method == 'POST':
        try:
            print("Raw body:", request.body)
            data = json.loads(request.body)
            logger.info(f"Received data: {data}")

            task_message = data.get('message', 'default message')
            mood_data, error_message = analyze_mood(user.username, task_message)

            # ✅ Save the mood entry
            MoodEntry.objects.create(
                user=user,
                message=task_message,
                mood=mood_data
            )

            return JsonResponse({
                "status": "success",
                "mood_data": mood_data,
                "error_message": error_message
            })

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return JsonResponse({"error": "Invalid request or data format."}, status=400)


    recent_moods = MoodEntry.objects.filter(user=user).order_by('-timestamp')[:5]  # Fetch recent moods

    # If it's a GET request, render the dashboard page
    context = {
        'tasks': tasks,
        'progress_percentage': progress_percentage,
        'mood_data': mood_data,
        'error_message': error_message,
        'recent_moods': recent_moods,  # Add recent moods to the context
    }

    return render(request, "dashboard.html", context)




def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()  # Save the updated task
            return redirect('dashboard')  # Redirect to the dashboard
    else:
        form = TaskForm(instance=task)  # Prepopulate the form with the task data

    return render(request, 'update_task.html', {'form': form, 'task': task})



@login_required
@require_POST
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    messages.info(request, "Task deleted!")
    return redirect('dashboard')


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    users = User.objects.annotate(task_count=Count('tasks'))

    total_users = users.count()
    total_tasks = Task.objects.count()

    context = {
        'users': users,
        'total_users': total_users,
        'total_tasks': total_tasks,
    }

    return render(request, 'admin_dashboard.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_user(request, user_id):
    if request.user.is_superuser:
        try:
            user = User.objects.get(id=user_id)
            user.delete()
            messages.success(request, f"User '{user.username}' deleted!")
        except User.DoesNotExist:
            messages.error(request, "User does not exist")
    return redirect('admin_dashboard')


def features(request):
    return render(request, 'features.html')


def resources(request):
    return render(request, 'resources.html')


def aboutus(request):
    return render(request, 'aboutus.html')






@login_required
def toggle_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.is_completed = not task.is_completed
    task.save()
    messages.success(request, f"Task '{task.name}' marked as {'completed' if task.is_completed else 'incomplete'}.")
    return redirect('dashboard')


def get_mood(request, username):
    flask_url = f'http://localhost:5000/get-mood-by-username?username={username}'

    try:
        # Sending GET request to Flask API
        response = requests.get(flask_url)

        if response.status_code == 200:
            # Return the mood data if successful
            mood_data = response.json()
            return render(request, 'mood_display.html', {'mood_data': mood_data})
        else:
            # Return error if the API call is unsuccessful
            return JsonResponse({"error": "Failed to fetch mood data from Flask API"}, status=400)

    except requests.exceptions.RequestException as e:
        # Log and return the error if the request fails
        logger.error(f"Error fetching mood data from Flask: {e}")
        return JsonResponse({"error": str(e)}, status=500)

