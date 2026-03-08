from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Sum, Count, Avg # Added Sum and Count
from django.utils import timezone # For accurate date tracking
from datetime import date,datetime

from .models import ChildProfile, Lesson, Assignment, Notification, ScreeningResult, ActivityProgress,LessonFeedback
from .utils import render_to_pdf

# Use custom User model
User = get_user_model()
# This variable now correctly points to YOUR accounts.User model

# --- AUTHENTICATION & CORE ---
# accounts/views.py
from django.views.decorators.cache import never_cache # Import this

# --- AUTHENTICATION & CORE ---

@never_cache # Add this decorator here
def home(request):
    """ 
    Ensures the home page always checks the current session 
    and never shows a 'cached' version of the login/logout buttons.
    """
    return render(request, 'home.html')

@never_cache # Also add to registration to prevent 'back-button' glitches

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


# accounts/views.py

# accounts/views.py

# accounts/views.py

def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Check if this is a Student account
            if user.role == 'student':
                # Link to the ChildProfile using the user relationship
                child_profile = getattr(user, 'child_profile', None)
                
                if child_profile:
                    # RESTRICTION: Block direct login for high sensitivity
                    if child_profile.autism_percentage >= 50:
                        messages.error(request, "Access Restricted: High sensitivity detected. Please log in through the Parent Gateway.")
                        return redirect('login')
                    
                    # SUCCESS: Direct login for low sensitivity
                    login(request, user)
                    request.session['active_child_id'] = child_profile.id # Set session for game tracking
                    return redirect('skill_selection_portal', child_id=child_profile.id)

            # Standard Logic for Parents/Admins
            if user.is_approved or user.is_superuser:
                login(request, user)
                return redirect('role_dashboard')
            else:
                messages.warning(request, "Account pending approval.")
                return redirect('login')
        else:
            messages.error(request, "Invalid credentials.")
            
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

# accounts/views.py

@login_required
def child_screening_test(request, child_id):
    """ Autism Readiness Screening Logic: Redirects based on score """
    child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
    
    if request.method == "POST":
        q_keys = ['q1', 'q2', 'q3', 'q4', 'q5']
        # Calculate sensitivity percentage
        yes_count = sum(1 for k in q_keys if request.POST.get(k) == 'yes')
        percentage = (yes_count / 5) * 100
        
        # Determine if high support is needed
        is_high = percentage >= 50
        
        # Save the result so the Login View can check it later
        ScreeningResult.objects.update_or_create(
            child=child, 
            defaults={'score_percentage': percentage, 'is_high_sensitivity': is_high}
        )
        
        if not is_high:
            messages.success(request, f"Readiness Score: {percentage}%. Child may log in directly.")
            return redirect('skill_selection_portal', child_id=child.id)
        else:
            messages.warning(request, f"Score: {percentage}%. High sensitivity detected. Direct login disabled. Please use Parent Gateway.")
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
    """ Separates Lessons from Activities for the UI """
    child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
    
    # 1. Fetch Instructional Content (Videos/PDFs)
    instructional_content = Lesson.objects.filter(
        skill_category=skill_slug, 
        is_activity=False, 
        is_approved=True
    )
    
    # 2. Fetch Interactive Content (Games)
    interactive_content = Lesson.objects.filter(
        skill_category=skill_slug, 
        is_activity=True, 
        is_approved=True
    )
    
    return render(request, 'accounts/child/skill_lessons.html', {
        'child': child,
        'skill_name': skill_slug.replace('_', ' ').title(),
        'lessons': instructional_content,
        'activities': interactive_content
    })
@login_required
def exit_child_gate(request):
    if 'active_child_id' in request.session:
        del request.session['active_child_id']
    return redirect('parent_dashboard')

# --- ADMIN SECTION (Module 1.0) ---
# accounts/views.py

# This fetches your custom 'accounts.User' model correctly
User = get_user_model() 

# accounts/views.py
# accounts/views.py
from django.db.models import Count
from django.utils import timezone

# accounts/views.py

@login_required
def admin_dashboard(request):
    if not (request.user.role == 'admin' or request.user.is_superuser):
        return HttpResponseForbidden()
    
    # 1. FIXED COUNTERS: Pulling fresh counts from SQLite
    total_parents = User.objects.filter(role='parent').count()
    total_contributors = User.objects.filter(role='contributor').count()
    total_approved = User.objects.filter(is_approved=True).exclude(id=request.user.id).count()
    
    # 2. TAB DATA: Populating User Directory and Content Queue
    pending_users = User.objects.filter(is_approved=False).exclude(id=request.user.id)
    approved_users_list = User.objects.filter(is_approved=True).exclude(id=request.user.id)
    pending_lessons = Lesson.objects.filter(is_approved=False)
    approved_lessons = Lesson.objects.filter(is_approved=True)

    # 3. DYNAMIC SKILLS: Pulls unique categories currently in the Lesson database
    db_cats = Lesson.objects.values_list('skill_category', flat=True).distinct()
    formatted_categories = [{'slug': c, 'name': c.replace('_', ' ').title()} for c in db_cats]

    return render(request, 'accounts/dashboards/admin_dashboard.html', {
        'total_parents': total_parents,
        'total_contributors': total_contributors,
        'total_approved': total_approved,
        'pending_users': pending_users,
        'approved_users_list': approved_users_list,
        'pending_lessons': pending_lessons,
        'approved_lessons': approved_lessons,
        'categories': formatted_categories,
        'today': timezone.now(),
    })

# --- MODERATION ACTIONS (Sticky Tab Logic) ---

@login_required
def approve_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_approved = True
    user.save()
    messages.success(request, f"User {user.email} is now active.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))

@login_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.error(request, "Account removed from the ecosystem.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))

@login_required
def request_module_update(request, lesson_id):
    """ DFD Process 1.0.2: Sending suggestions back to Contributors """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    Notification.objects.create(
        user=lesson.contributor, # Crash occurs here
        message=f"Admin suggests an update for your module: {lesson.title}"
)
    messages.info(request, f"Update request sent to {lesson.contributor.first_name}.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))

@login_required
def delete_module(request, lesson_id):
    """ Removes specific content from the platform """
    get_object_or_404(Lesson, id=lesson_id).delete()
    messages.error(request, "Module permanently deleted.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))
@login_required
def reject_user(request, user_id):
    get_object_or_404(User, id=user_id).delete()
    return redirect('admin_dashboard')

"""@login_required
def approve_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if request.method == 'POST':
        lesson.admin_feedback = request.POST.get('admin_feedback')
    lesson.is_approved = True
    lesson.save()
    return redirect('admin_dashboard')"""
# accounts/views.py

@login_required
def approve_lesson(request, lesson_id):
    if not (request.user.role == 'admin' or request.user.is_superuser):
        return HttpResponseForbidden()
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    action = request.POST.get('action')
    notes = request.POST.get('admin_notes', '')

    if action == 'approve':
        lesson.is_approved = True
        lesson.admin_notes = "" # Clear any old rejection notes
        messages.success(request, f"Module '{lesson.title}' is now live!")
    
    elif action == 'reject':
        lesson.is_approved = False
        lesson.admin_notes = notes # Save the reason for rejection
        
        # Notify the contributor (Process 1.0.2)
        Notification.objects.create(
            user=lesson.contributor,
            message=f"Revision Required: '{lesson.title}'. Reason: {notes}"
        )
        messages.warning(request, f"Module '{lesson.title}' rejected with feedback.")

    lesson.save()
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))


@login_required
def manage_categories(request):
    categories = Lesson.objects.values_list('skill_category', flat=True).distinct()
    return render(request, 'accounts/admin/manage_categories.html', {'categories': categories})

@login_required
def manage_difficulty(request):
    return render(request, 'accounts/admin/manage_difficulty.html')

@login_required
def view_analytics(request):
    if not (request.user.role == 'admin' or request.user.is_superuser):
        return HttpResponseForbidden()

    # Calculate Top Lesson based on actual completions (ActivityProgress)
    top_lesson = Lesson.objects.annotate(
        completion_count=Count('activityprogress')
    ).order_by('-completion_count').first()

    return render(request, 'accounts/admin/analytics.html', {
        'total_lessons': Lesson.objects.count(),
        'completed_tasks': ActivityProgress.objects.count(),
        'top_lesson': top_lesson,
        'total_users': User.objects.count(),
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
# accounts/views.py

# accounts/views.py

# accounts/views.py
@login_required
def contributor_dashboard(request):
    """ Updated to track actual student engagement (completions). """
    lessons = Lesson.objects.filter(contributor=request.user)
    
    # 1. Real Tracking: Count how many times these lessons were actually completed
    engagement_count = ActivityProgress.objects.filter(lesson__in=lessons).count()
    
    # 2. Moderated Feedback Relay
    moderated_feedback = LessonFeedback.objects.filter(
        lesson__contributor=request.user, 
        is_moderated=True
    ).order_by('-created_at')
    
    return render(request, 'accounts/dashboards/contributor_dashboard.html', {
        'lessons': lessons,
        'moderated_feedback': moderated_feedback,
        'approved_count': lessons.filter(is_approved=True).count(),
        'total_views': engagement_count, # This now shows real student progress
    })
@login_required
def upload_lesson(request):
    """ Feature: Content Creation with support for Files and YouTube URLs """
    if request.user.role.lower() != 'contributor':
        return HttpResponseForbidden("Access Denied: Contributors Only")

    if request.method == 'POST':
        # 1. Extract Basic Metadata
        title = request.POST.get('title')
        skill_category = request.POST.get('skill_category')
        target_age = request.POST.get('target_age')
        
        # Capture the new YouTube URL field
        video_url = request.POST.get('video_url')
        
        # Handle empty numeric/choice fields
        duration = request.POST.get('duration') or 0
        difficulty = request.POST.get('difficulty_level') or 'beginner'
        
        # 2. Extract Professional Content Insights
        objectives = request.POST.get('objectives')
        description = request.POST.get('description')
        
        # Logic: Auto-set content type if YouTube URL is present
        content_type = request.POST.get('content_type')
        if video_url:
            content_type = 'youtube'

        # 3. Capture the Activity Toggle
        is_activity = request.POST.get('is_activity') == 'on'

        # 4. Create the Lesson Record
        lesson = Lesson.objects.create(
            contributor=request.user,
            title=title,
            duration_minutes=duration,
            skill_category=skill_category,
            target_age_group=target_age,
            difficulty_level=difficulty,
            learning_objectives=objectives,
            description=description,
            content_type=content_type,
            is_activity=is_activity,           
            file=request.FILES.get('file'),         # Can be null if using YouTube
            video_url=video_url,                    # New field
            thumbnail=request.FILES.get('thumbnail'),
            is_approved=False                      
        )

        type_label = "Activity" if is_activity else "Lesson"
        messages.success(request, f"{type_label} '{title}' submitted successfully for Admin approval!")
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
# --- Add these new functions to your views.py ---

@login_required
def child_login_redirect(request, child_id):
    """
    Checks the saved autism percentage from the one-time registration 
    screening to determine the login path.
    """
    child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
    
    # If percentage is above 50, redirect to separate student login/verification
    if child.autism_percentage >= 50:
        messages.info(request, "High sensitivity profile detected. Accessing Student Portal.")
        return redirect('student_login_page', child_id=child.id)
    
    # If below 50, redirect to your Skill Portal page
    return redirect('skill_selection_portal', child_id=child.id)


# --- Update your existing add_child function to trigger screening immediately ---

"""@login_required
def add_child(request):
    if request.user.role.lower() != 'parent':
        return HttpResponseForbidden("Access Denied")
    if request.method == 'POST':
        # Create the child profile first
        child = ChildProfile.objects.create(
            parent=request.user,
            name=request.POST.get('name'),
            age=request.POST.get('age'),
            learning_style=request.POST.get('learning_style'),
            sensory_mode=request.POST.get('sensory_mode'),
            diagnosis=request.POST.get('diagnosis'),
            reward_preference=request.POST.get('reward_pref'),
            notes=request.POST.get('notes')
        )
        messages.success(request, "Basic profile created. Please complete the initial screening.")
        
        # REDIRECT: Go to the one-time screening test immediately
        return redirect('child_screening_test', child_id=child.id)
    
    return render(request, 'accounts/child/add_child.html')"""


# --- Update your child_screening_test to save results permanently ---

@login_required
def child_screening_test(request, child_id):
    """ One-time Autism Readiness Screening during registration """
    child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
    if request.method == "POST":
        q_keys = ['q1', 'q2', 'q3', 'q4', 'q5']
        yes_count = sum(1 for k in q_keys if request.POST.get(k) == 'yes')
        percentage = (yes_count / 5) * 100
        
        # Logic: Save results permanently to the Child model
        child.autism_percentage = percentage
        child.is_high_sensitivity = (percentage >= 50)
        child.save()
        
        # Also log to ScreeningResult table for reporting history
        ScreeningResult.objects.create(child=child, score_percentage=percentage, is_high_sensitivity=child.is_high_sensitivity)
        
        messages.success(request, f"Registration complete! Autism Percentage: {percentage}%")
        return redirect('parent_dashboard')
            
    return render(request, 'accounts/parent/screening_test.html', {'child': child})
def student_login_view(request):
    """ Standard login page specifically for Student entry """
    if request.method == "POST":
        # Capture credentials (can be parent's or unique student account)
        user = authenticate(request, 
                            username=request.POST.get('username'), 
                            password=request.POST.get('password'))
        
        if user is not None and (user.role == 'parent' or user.is_superuser):
            login(request, user)
            
            # Fetch the specific student requested (assuming student name/ID is passed)
            # For simplicity, we fetch the first child. In production, use a PIN selector.
            child = user.children.first() 
            
            if child:
                # APPLY LOGIC: Check saved percentage from registration
                if child.autism_percentage >= 50:
                    return redirect('student_login_page', child_id=child.id)
                else:
                    return redirect('skill_selection_portal', child_id=child.id)
            return redirect('parent_dashboard')
            
        else:
            messages.error(request, "Invalid student credentials.")
            
    return render(request, 'accounts/child/login.html')
# accounts/views.py
# To ensure both User and Profile are created together

@login_required
def add_child(request):
    """ Creates both a Child User account and a Child Profile """
    if request.user.role.lower() != 'parent':
        return HttpResponseForbidden("Access Denied")
        
    if request.method == 'POST':
        s_username = request.POST.get('student_username')
        s_password = request.POST.get('student_password')

        # Check for existing username using the active User model
        if User.objects.filter(username=s_username).exists():
            messages.error(request, "This student username is already taken. Try another.")
            return render(request, 'accounts/child/add_child.html')

        # Calculate initial Autism Percentage from the 5 questions
        q_keys = ['q1', 'q2', 'q3', 'q4', 'q5']
        yes_count = sum(1 for key in q_keys if request.POST.get(key) == 'yes')
        percentage = (yes_count / 5) * 100
        high_sensitivity = (percentage >= 50)

        try:
            with transaction.atomic():
                # Create the student user with the correct role
                child_user = User.objects.create_user(
                    username=s_username, 
                    password=s_password,
                    role='student'  # CRITICAL: Ensures role-based login works
                )
                
                # Create the profile linked to the new student user
                child = ChildProfile.objects.create(
                    user=child_user,
                    parent=request.user,
                    name=request.POST.get('name'),
                    age=request.POST.get('age'),
                    learning_style=request.POST.get('learning_style'),
                    sensory_mode=request.POST.get('sensory_mode'),
                    diagnosis=request.POST.get('diagnosis'),
                    reward_preference=request.POST.get('reward_pref'),
                    notes=request.POST.get('notes'),
                    autism_percentage=percentage,
                    is_high_sensitivity=high_sensitivity
                )
                
                # Record result in history
                ScreeningResult.objects.create(
                    child=child, 
                    score_percentage=percentage, 
                    is_high_sensitivity=high_sensitivity
                )

            messages.success(request, f"Profile created for {s_username}! Score: {percentage}%")
            return redirect('parent_dashboard')
            
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
        
    return render(request, 'accounts/child/add_child.html')
@login_required
def edit_child(request, child_id):
    """ Feature: Edit existing student profile """
    child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
    if request.method == 'POST':
        child.name = request.POST.get('name')
        child.age = request.POST.get('age')
        child.learning_style = request.POST.get('learning_style')
        child.sensory_mode = request.POST.get('sensory_mode')
        child.diagnosis = request.POST.get('diagnosis')
        child.notes = request.POST.get('notes')
        child.save()
        messages.success(request, f"Profile for {child.name} updated.")
        return redirect('child_list')
    return render(request, 'accounts/child/edit_child.html', {'child': child})

@login_required
def remove_child(request, child_id):
    """ Feature: Remove student profile from system """
    child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
    child_name = child.name
    child.delete()
    messages.error(request, f"Profile for {child_name} has been removed.")
    return redirect('child_list')

@login_required
def save_parent_feedback(request, child_id):
    """ Feature: Log behavioral feedback/milestones """
    if request.method == 'POST':
        child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
        # Update the 'notes' or create a dedicated Feedback model entry
        new_feedback = request.POST.get('parent_notes')
        child.notes = f"{child.notes}\n---\nFeedback ({date.today()}): {new_feedback}"
        child.save()
        messages.success(request, "Feedback saved and forwarded to system analytics.")
    return redirect('child_list')
# accounts/views.py

@login_required
def skill_lessons_view(request, child_id, skill_slug):
    child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
    
    base_query = Lesson.objects.filter(skill_category=skill_slug, is_approved=True)
    
    # Ensure these filters match your Lesson model fields
    lessons = base_query.filter(is_activity=False)
    activities = base_query.filter(is_activity=True) 
    
    return render(request, 'accounts/child/skill_lessons.html', {
        'child': child,
        'skill_name': skill_slug.replace('_', ' ').title(),
        'lessons': lessons,
        'activities': activities,
    })
# accounts/views.py

@login_required
def system_activity_player(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    mode = request.GET.get('mode', 'view')
    
    # Check if a child is active in the session
    child = None
    if 'active_child_id' in request.session:
        child = get_object_or_404(ChildProfile, id=request.session['active_child_id'])
    
    # If no child (Admin Preview), we can still render the page
    return render(request, 'accounts/child/system_player.html', {
        'lesson': lesson,
        'mode': mode,
        'child': child,
        'is_admin': request.user.is_superuser # Used to hide "Save Progress" buttons
    })


@login_required
def record_completion(request, lesson_id):
    """ Records student progress and returns real-time star totals """
    if request.method == 'POST':
        child_id = request.session.get('active_child_id')
        if not child_id:
            return JsonResponse({'status': 'error', 'message': 'No active child session'}, status=400)
            
        child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        # Save a new record every time a child finishes to track practice
        progress = ActivityProgress.objects.create(
            child=child, 
            lesson=lesson,
            stars_earned=3 
        )
        
        # Calculate fresh totals for the player UI
        total_stars = ActivityProgress.objects.filter(child=child).aggregate(Sum('stars_earned'))['stars_earned__sum'] or 0
        
        return JsonResponse({
            'status': 'success', 
            'stars_earned': progress.stars_earned,
            'total_stars': total_stars
        })
# accounts/views.py
# accounts/views.py
# accounts/views.py

@login_required
def parent_report_view(request, child_id):
    """ Dynamically calculates totals for the Progress Report UI """
    # Security: Only the parent of this child can view the report
    child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
    
    # Fetch records and pre-fetch lesson data for performance
    progress_records = ActivityProgress.objects.filter(child=child).select_related('lesson').order_by('-completed_at')
    
    # Calculate live dashboard metrics
    total_stars = progress_records.aggregate(Sum('stars_earned'))['stars_earned__sum'] or 0
    activities_count = progress_records.count()
    
    return render(request, 'accounts/parent/report.html', {
        'child': child,
        'records': progress_records, 
        'total_stars': total_stars,      # Matches template {{ total_stars }}
        'activities_count': activities_count # Matches template {{ activities_count }}
    })

@login_required
def download_progress_report(request, child_id):
    child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
    records = ActivityProgress.objects.filter(child=child).select_related('lesson')
    
    context = {
        'child': child,
        'records': records,
        'total_stars': records.aggregate(Sum('stars_earned'))['stars_earned__sum'] or 0,
        'date': datetime.now(), # Uses the corrected import
    }
    
    pdf = render_to_pdf('accounts/parent/report_pdf_template.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Report_{child.name}_{datetime.now().date()}.pdf"
        response['Content-Disposition'] = f"attachment; filename='{filename}'"
        return response
    return HttpResponse("Error generating PDF", status=400)
@login_required
def remove_account(request, user_id):
    """ Deletes user and logs a reason """
    if not request.user.is_superuser:
        return HttpResponseForbidden()
        
    user_to_delete = get_object_or_404(User, id=user_id)
    reason = request.POST.get('reason', 'Violation of terms.')
    
    # Logic: Delete user
    user_to_delete.delete()
    messages.error(request, f"Account {user_to_delete.email} removed. Reason: {reason}")
    return redirect('admin_dashboard')
# accounts/views.py

@login_required
def submit_lesson_feedback(request):
    """ Allows parents to report sensory issues or helpfulness to the Admin """
    if request.method == "POST":
        lesson_id = request.POST.get('lesson_id')
        message = request.POST.get('message')
        
        if not lesson_id or not message:
            messages.error(request, "Please select a lesson and provide feedback.")
            return redirect(request.META.get('HTTP_REFERER', 'parent_dashboard'))
            
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        # Save feedback as 'unmoderated' by default
        LessonFeedback.objects.create(
            lesson=lesson,
            parent=request.user,
            message=message,
            is_moderated=False
        )
        
        messages.success(request, "Your feedback has been sent to the System Controller for review.")
    return redirect(request.META.get('HTTP_REFERER', 'parent_dashboard'))
# accounts/views.py

@login_required
def relay_feedback_to_contributor(request, feedback_id):
    """ Admin approves and forwards parent feedback to the content creator """
    if not (request.user.role == 'admin' or request.user.is_superuser):
        return HttpResponseForbidden()
        
    feedback = get_object_or_404(LessonFeedback, id=feedback_id)
    feedback.is_moderated = True
    feedback.save()
    
    messages.success(request, f"Feedback for '{feedback.lesson.title}' forwarded to Contributor.")
    return redirect('admin_dashboard')
# accounts/views.py
from django.db.models import Sum

@login_required
def record_completion(request, lesson_id):
    """
    Core System: Records student progress and grants rewards (stars).
    Triggered via AJAX from the system_player.html when an activity finishes.
    """
    if request.method == 'POST':
        child_id = request.session.get('active_child_id')
        if not child_id:
            return JsonResponse({'status': 'error', 'message': 'No active child session'}, status=400)
            
        child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        # Record the progress. We use create instead of get_or_create 
        # to allow children to practice and earn stars multiple times.
        progress = ActivityProgress.objects.create(
            child=child, 
            lesson=lesson,
            stars_earned=3 # Reward for successful completion
        )
        
        # Calculate total stars for real-time UI updates
        total_stars = ActivityProgress.objects.filter(child=child).aggregate(Sum('stars_earned'))['stars_earned__sum'] or 0
        
        return JsonResponse({
            'status': 'success', 
            'stars_earned': progress.stars_earned,
            'total_stars': total_stars
        })
# accounts/views.py

@login_required
def send_notifications(request):
    if request.method == "POST":
        target_roles = request.POST.getlist('target') # Gets ['parent', 'contributor']
        msg_text = request.POST.get('message')
        
        # Dispatch to everyone matching the selected roles
        users_to_notify = User.objects.filter(role__in=target_roles)
        for user in users_to_notify:
            Notification.objects.create(user=user, message=msg_text)
            
        messages.success(request, f"Broadcast sent to {users_to_notify.count()} users.")
        return redirect('admin_dashboard')
# accounts/views.py

@login_required
def edit_lesson(request, lesson_id):
    """ Allows contributors to modify content and clear admin rejection notes """
    lesson = get_object_or_404(Lesson, id=lesson_id, contributor=request.user)
    
    if request.method == "POST":
        lesson.title = request.POST.get('title')
        lesson.skill_category = request.POST.get('skill_category')
        lesson.difficulty_level = request.POST.get('difficulty_level')
        lesson.content_type = request.POST.get('content_type')
        lesson.description = request.POST.get('description')
        
        # LOGIC: Reset approval and clear old notes for resubmission
        lesson.is_approved = False 
        lesson.admin_notes = "" 
        
        # Update files/URLs if provided
        if request.FILES.get('file'):
            lesson.file = request.FILES.get('file')
        if request.POST.get('video_url'):
            lesson.video_url = request.POST.get('video_url')
            
        lesson.save()
        messages.success(request, f"Changes saved. '{lesson.title}' is back in the review queue.")
        return redirect('contributor_dashboard')
        
    return render(request, 'accounts/dashboards/edit_lesson.html', {'lesson': lesson})
# accounts/views.py

@login_required
def skill_lessons_view(request, child_id, skill_slug):
    child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
    
    # Base Query
    base_query = Lesson.objects.filter(skill_category=skill_slug, is_approved=True)
    
    # NEW: Sorting/Filtering Logic
    difficulty_filter = request.GET.get('difficulty')
    if difficulty_filter:
        base_query = base_query.filter(difficulty_level=difficulty_filter)
    
    lessons = base_query.filter(is_activity=False)
    activities = base_query.filter(is_activity=True) 
    
    return render(request, 'accounts/child/skill_lessons.html', {
        'child': child,
        'skill_name': skill_slug.replace('_', ' ').title(),
        'lessons': lessons,
        'activities': activities,
        'current_difficulty': difficulty_filter,
    })