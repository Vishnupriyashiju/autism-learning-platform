from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import User, ChildProfile, Lesson, Assignment, Notification, ScreeningResult

# --- AUTHENTICATION & CORE ---
def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == "POST":
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        dob = request.POST.get('dob')
        role = request.POST.get('role')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect('register')

        user = User.objects.create_user(
            username=email, email=email, phone=phone,
            role=role, dob=dob, password=password
        )
        user.first_name = full_name
        user.save()

        login(request, user)
        return redirect('role_dashboard')
    return render(request, 'accounts/register.html')

def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_approved or user.is_superuser:
                login(request, user)
                return redirect('role_dashboard')
            else:
                messages.warning(request, "Your account is pending administrator approval.")
                return redirect('login')
        else:
            messages.error(request, "Invalid username or password")
            return redirect('login')
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def role_dashboard(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    role = request.user.role.lower().strip()
    if role == 'parent':
        return redirect('parent_dashboard')
    elif role == 'admin':
        return redirect('admin_dashboard')
    elif role == 'contributor':
        return redirect('contributor_dashboard')
    else:
        return HttpResponseForbidden(f"Invalid role configuration: '{role}'")

# --- PARENT SECTION ---
@login_required
def parent_dashboard(request):
    if request.user.role.lower() != 'parent':
        return HttpResponseForbidden("Access Denied")
    children = request.user.children.all()
    approved_lessons = Lesson.objects.filter(is_approved=True)
    return render(request, 'accounts/dashboards/parent_dashboard.html', {
        'child_count': children.count(),
        'children': children,
        'approved_lessons': approved_lessons
    })

@login_required
def child_list(request):
    if request.user.role.lower() != 'parent':
        return HttpResponseForbidden("Access Denied")
    children = request.user.children.all()
    return render(request, 'accounts/child/child_list.html', {'children': children})

@login_required
def add_child(request):
    if request.user.role.lower() != 'parent':
        return HttpResponseForbidden("Access Denied")
    if request.method == 'POST':
        ChildProfile.objects.create(
            parent=request.user,
            name=request.POST.get('name'),
            age=request.POST.get('age'),
            learning_style=request.POST.get('learning_style'),
            sensory_mode=request.POST.get('sensory_mode'),
            diagnosis=request.POST.get('diagnosis'),
            reward_preference=request.POST.get('reward_pref'),
            notes=request.POST.get('notes')
        )
        messages.success(request, "Student profile created successfully!")
        return redirect('child_list')
    return render(request, 'accounts/child/add_child.html')

# --- CHILD PORTAL & SCREENING ---
@login_required
def child_dashboard(request, child_id):
    """ Fixed the missing attribute error """
    child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
    task = Assignment.objects.filter(child=child, is_completed=False).first()
    return render(request, 'accounts/child/dashboard.html', {
        'child': child,
        'task': task,
        'sensory_mode': child.sensory_mode
    })

@login_required
def child_screening_test(request, child_id):
    """ Autism Readiness Screening Logic """
    child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
    if request.method == "POST":
        q_keys = ['q1', 'q2', 'q3', 'q4', 'q5']
        yes_count = sum(1 for k in q_keys if request.POST.get(k) == 'yes')
        percentage = (yes_count / 5) * 100
        is_high = percentage >= 50
        ScreeningResult.objects.create(child=child, score_percentage=percentage, is_high_sensitivity=is_high)
        if not is_high:
            messages.success(request, f"Readiness Score: {percentage}%. Access granted.")
            return redirect('skill_selection_portal', child_id=child.id)
        else:
            messages.warning(request, "High sensitivity detected. Parent verification required.")
            return redirect('parent_dashboard')
    return render(request, 'accounts/parent/screening_test.html', {'child': child})

@login_required
def launch_child_gate(request, child_id):
    """ Captures daily mood/IQ and redirects to Portal """
    if request.method == "POST":
        child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
        request.session['target_mood'] = request.POST.get('target_mood')
        request.session['iq_focus'] = request.POST.get('iq_focus')
        return redirect('skill_selection_portal', child_id=child.id)
    return redirect('parent_dashboard')
@login_required
def skill_selection_portal(request, child_id):
    """ Renders the full-page 9-icon grid """
    child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
    request.session['active_child_id'] = child.id
    
    # Passing this list directly avoids the TemplateSyntaxError
    skill_list = [
        {'slug': 'behavioral', 'name': 'Behavioral', 'icon': 'fa-brain'},
        {'slug': 'communication', 'name': 'Communication', 'icon': 'fa-comments'},
        {'slug': 'social', 'name': 'Social', 'icon': 'fa-users'},
        {'slug': 'cognitive', 'name': 'Cognitive', 'icon': 'fa-lightbulb'},
        {'slug': 'motor', 'name': 'Motor', 'icon': 'fa-running'},
        {'slug': 'sensory', 'name': 'Sensory', 'icon': 'fa-hand-sparkles'},
        {'slug': 'academic', 'name': 'Academic', 'icon': 'fa-book-reader'},
        {'slug': 'self_care', 'name': 'Self-Care', 'icon': 'fa-heart'},
        {'slug': 'vocal', 'name': 'Vocal', 'icon': 'fa-microphone'},
    ]
    
    return render(request, 'accounts/child/skill_portal.html', {
        'child': child,
        'skills': skill_list
    })

@login_required
def skill_lessons_view(request, child_id, skill_slug):
    child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
    lessons = Lesson.objects.filter(skill_category=skill_slug, is_approved=True)
    return render(request, 'accounts/child/skill_lessons.html', {
        'child': child,
        'skill_name': skill_slug.replace('_', ' ').title(),
        'lessons': lessons
    })

@login_required
def exit_child_gate(request):
    if 'active_child_id' in request.session:
        del request.session['active_child_id']
    return redirect('parent_dashboard')

# --- ADMIN SECTION (Module 1.0) ---
@login_required
def admin_dashboard(request):
    if not (request.user.role == 'admin' or request.user.is_superuser):
        return HttpResponseForbidden()
    return render(request, 'accounts/dashboards/admin_dashboard.html', {
        'total_parents': User.objects.filter(role='parent').count(),
        'total_contributors': User.objects.filter(role='contributor').count(),
        'total_approved': User.objects.filter(is_approved=True).count(),
        'pending_users': User.objects.filter(is_approved=False).exclude(id=request.user.id),
        'pending_lessons': Lesson.objects.filter(is_approved=False)
    })

@login_required
def approve_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_approved = True
    user.save()
    return redirect('admin_dashboard')

@login_required
def reject_user(request, user_id):
    get_object_or_404(User, id=user_id).delete()
    return redirect('admin_dashboard')

@login_required
def approve_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if request.method == 'POST':
        lesson.admin_feedback = request.POST.get('admin_feedback')
    lesson.is_approved = True
    lesson.save()
    return redirect('admin_dashboard')

@login_required
def manage_categories(request):
    categories = Lesson.objects.values_list('skill_category', flat=True).distinct()
    return render(request, 'accounts/admin/manage_categories.html', {'categories': categories})

@login_required
def manage_difficulty(request):
    return render(request, 'accounts/admin/manage_difficulty.html')

@login_required
def view_analytics(request):
    return render(request, 'accounts/admin/analytics.html', {
        'total_lessons': Lesson.objects.count(),
        'completed_tasks': Assignment.objects.filter(is_completed=True).count(),
        'top_lesson': Lesson.objects.order_by('-views_count').first(),
    })

@login_required
def send_notifications(request):
    if request.method == "POST":
        Notification.objects.create(message=request.POST.get('message'))
        messages.success(request, "Notification sent!")
        return redirect('admin_dashboard')
    return render(request, 'accounts/admin/notifications.html')

@login_required
def platform_config(request):
    return render(request, 'accounts/admin/platform_config.html')

# --- CONTRIBUTOR & ACTIVITY ---
@login_required
def contributor_dashboard(request):
    lessons = Lesson.objects.filter(contributor=request.user)
    return render(request, 'accounts/dashboards/contributor_dashboard.html', {'lessons': lessons})

@login_required
def upload_lesson(request):
    if request.method == 'POST':
        Lesson.objects.create(
            contributor=request.user,
            title=request.POST.get('title'),
            skill_category=request.POST.get('skill_category'),
            difficulty_level=request.POST.get('difficulty_level'),
            file=request.FILES.get('file')
        )
        return redirect('contributor_dashboard')
    return render(request, 'accounts/dashboards/upload_lesson.html')

@login_required
def complete_activity(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    assignment.is_completed = True
    assignment.save()
    return redirect('child_dashboard', child_id=assignment.child.id)

@login_required
def system_activity_player(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    return render(request, 'accounts/child/system_player.html', {
        'child': assignment.child,
        'lesson': assignment.lesson,
        'game_type': assignment.lesson.activity_type, 
    })