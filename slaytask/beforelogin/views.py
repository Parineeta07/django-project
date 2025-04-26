from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .forms import TaskForm
from .models import Task
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import models
from django.db.models import Count
from django.views.decorators.http import require_POST


def homePage(request):
    return render(request, 'home.html')

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
                if user.is_superuser:
                    return redirect('admin_dashboard')
                else:
                    return redirect('dashboard')
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
            return redirect('login')  # ✅ this return must be inside the 'else' block

    return render(request, 'signup.html')
@login_required
def dashboard_view(request):
    tasks = Task.objects.filter(user=request.user)

    completed_tasks_count = tasks.filter(is_completed=True).count()
    pending_tasks_count = tasks.filter(is_completed=False).count()
    upcoming_tasks_count = tasks.filter(due_date__gte=timezone.now()).count()

    total_tasks = tasks.count()
    progress_percentage = (completed_tasks_count / total_tasks * 100) if total_tasks > 0 else 0

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, "Task added!")
            return redirect('dashboard')
    else:
        form = TaskForm()

    context = {
        'tasks': tasks,
        'form': form,
        'completed_tasks_count': completed_tasks_count,
        'pending_tasks_count': pending_tasks_count,
        'upcoming_tasks_count': upcoming_tasks_count,
        'progress_percentage': progress_percentage,  # ✅ Make sure this is passed
    }

    return render(request, 'dashboard.html', context)


    context = {
        'tasks': tasks,
        'form': form,
        'completed_tasks_count': completed_tasks_count,
        'pending_tasks_count': pending_tasks_count,
        'upcoming_tasks_count': upcoming_tasks_count,
    }

    return render(request, 'dashboard.html', context)



def update_task(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    form = TaskForm(instance=task)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('dashboard')

    return render(request, 'update_task.html', {'form': form})

@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == 'POST':
        task.completed = not task.completed
        task.save()
        return redirect('dashboard')


def toggle_task(request, task_id):
    # Get the task to be updated
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    # Toggle the task completion status
    task.is_completed = not task.is_completed
    task.save()

    # Recalculate the counts for completed and pending tasks
    completed_tasks_count = Task.objects.filter(user=request.user, is_completed=True).count()
    pending_tasks_count = Task.objects.filter(user=request.user, is_completed=False).count()
    upcoming_tasks_count = Task.objects.filter(user=request.user, due_date__gte=timezone.now()).count()

    # Redirect to the dashboard view with updated task counts
    return redirect('dashboard')
    
@login_required
@require_POST
def delete_task(request, task_id):
    task = Task.objects.get(id=task_id, user=request.user)
    task.delete()
    messages.info(request, "Task deleted!")
    return redirect('dashboard')

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    # Get all users with a count of their tasks
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
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    # Only allow deletion if the user is owner or an admin
    if request.user == task.user or request.user.is_superuser:
        task.delete()

    return redirect('admin_dashboard')  # or wherever you want to go next

@login_required
def delete_user(request, user_id):
    if request.user.is_superuser:
        try:
            user = User.objects.get(id=user_id)
            user.delete()
        except User.DoesNotExist:
            pass  # Optional: handle error gracefully
    return redirect('admin_dashboard')

def features(request):
    return render(request, 'features.html')

def resources(request):
    return render(request, 'resources.html')
    
def aboutus(request):
    return render(request, 'aboutus.html')
    
