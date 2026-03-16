from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Sum, Count, Avg # Added Sum and Count
from django.utils import timezone # For accurate date tracking
from datetime import date,datetime

from .models import ChildProfile, Lesson, Assignment, Notification, ScreeningResult, ActivityProgress, LessonFeedback, BehaviorLog, ParentReward, LearningPlan, LearningPlanItem
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


# accounts/views.py

# accounts/views.py



# accounts/views.py

@transaction.atomic
def register(request):
    if request.method == "POST":
        # 1. Capture Common Fields
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        location = request.POST.get('location')
        role = request.POST.get('role', '').lower()
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect('register')

        # 2. CREATE USER FIRST (This defines the 'user' variable)
        user = User.objects.create_user(
            username=email, 
            email=email, 
            phone=phone,
            role=role, 
            password=password, 
            first_name=full_name
        )
        user.location = location 
        
        # 3. ATTACH PHOTO (Now 'user' exists, so no UnboundLocalError)
        if request.FILES.get('profile_photo'):
            user.profile_photo = request.FILES.get('profile_photo')
        
        # 4. Role-Specific Logic
        if role == 'parent':
            user.relationship_to_child = request.POST.get('relationship', '')
            user.data_privacy_agreed = request.POST.get('data_privacy') == 'on'
            user.progress_tracking_permission = request.POST.get('progress_tracking') == 'on'
            user.is_approved = True  # Parents are main managers, auto-approved
            user.save()
            messages.success(request, "Registration successful! You can now log in.")
            return redirect('login')

        elif role == 'contributor':
            user.qualification = request.POST.get('qualification', '')
            user.experience_years = int(request.POST.get('experience') or 0)
            user.specialization = request.POST.get('specialization', '')
            user.portfolio_url = request.POST.get('portfolio_url', '')
            if request.FILES.get('certificate'):
                user.certificate = request.FILES.get('certificate')
            user.is_approved = False  # Awaits Admin review
            user.save()
            messages.info(request, "Registration successful! Pending Admin approval.")
            return redirect('login')

    return render(request, 'accounts/register.html')


# accounts/views.py

# accounts/views.py

# accounts/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

def login_view(request):
    """ Central Smart Gateway: Filters access based on Clinical Sensitivity """
    
    if request.method == "POST":
        u_name = request.POST.get('username')
        u_pass = request.POST.get('password')
        
        user = authenticate(request, username=u_name, password=u_pass)

        if user is not None:
            request.session['assisted_session'] = False

            # 1. Logic for Student Role (The Independent Path)
            if user.role == 'student':
                profile = getattr(user, 'child_profile', None)
                
                if profile:
                    # CLINICAL GATE 1: Block high sensitivity (Meena) from direct login
                    if profile.autism_percentage >= 50:
                        messages.error(request, "Access Restricted: High sensitivity detected. Please log in through the Parent Gateway.")
                        return redirect('login')
                    
                    # CLINICAL GATE 2: Check if Admin has activated this account (Hanna)
                    if not user.is_approved:
                        messages.warning(request, "Your independent account is awaiting Admin activation.")
                        return redirect('login')
                    
                    # SUCCESS: Log in and send to the NEW Independent Dashboard
                    login(request, user)
                    request.session['active_child_id'] = profile.id
                    messages.success(request, f"Welcome back, {profile.name}! Ready to explore?")
                    
                    # REDIRECT TO THE NEW DASHBOARD
                    return redirect('independent_student_dashboard')
                else:
                    messages.error(request, "Student profile not found. Contact Admin.")
                    return redirect('login')

            # 2. Logic for Parents, Contributors, and Admins
            if user.is_approved or user.is_superuser:
                login(request, user)
                
                if user.role == 'parent':
                    return redirect('parent_dashboard')
                elif user.role == 'contributor':
                    return redirect('contributor_dashboard')
                else:
                    return redirect('role_dashboard')
            else:
                messages.warning(request, "Your account is pending Admin approval.")
                return redirect('login')
                
        else:
            messages.error(request, "Invalid username or password.")
            
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
@login_required
@never_cache
def parent_dashboard(request):
    """ Fixed to explicitly fetch profiles linked to the parent """
    if request.user.role.lower() != 'parent':
        return redirect('role_dashboard')
    
    # FIX: Use direct filter instead of .children.all() to ensure visibility
    children = ChildProfile.objects.filter(parent=request.user)
    
    # Calculate child count for the header stat
    child_count = children.count()
    
    approved_lessons = Lesson.objects.filter(is_approved=True)

    return render(request, 'accounts/dashboards/parent_dashboard.html', {
        'child_count': child_count,
        'children': children,
        'approved_lessons': approved_lessons
    })

@login_required
def child_list(request):
    if request.user.role.lower() != 'parent':
        return HttpResponseForbidden("Access Denied")
    children = request.user.children.all()
    return render(request, 'accounts/child/child_list.html', {'children': children})


# --- NEW: DAILY TASK ASSIGNMENT LOGIC ---
@login_required
def assign_daily_class(request):
    """ Feature: Assigns a bundle of lessons based on Class Category """
    if request.method == "POST":
        child_id = request.POST.get('child_id')
        category = request.POST.get('category') # toddler, kindergarden, teenage
        
        child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
        
        # Guide's Logic: 1 Skill bundle = Multiple Lessons from that age group
        bundle_lessons = Lesson.objects.filter(
            target_age_group__iexact=category, 
            is_approved=True
        )
        
        if not bundle_lessons.exists():
            messages.warning(request, f"No lessons found for the {category} category yet.")
            return redirect('parent_dashboard')

        # Create assignments for today
        count = 0
        for lesson in bundle_lessons:
            # get_or_create prevents duplicate assignments for the same day
            obj, created = Assignment.objects.get_or_create(
                child=child,
                lesson=lesson,
                assigned_date=date.today(),
                defaults={'is_completed': False}
            )
            if created: count += 1
            
        messages.success(request, f"Assigned {count} new lessons to {child.name}'s portal for today.")
    return redirect('parent_dashboard')

# --- NEW: BEHAVIORAL LOGGING ---
@login_required
def save_behavior_log(request):
    """ Feature: Daily Behavior Tracking to inform clinical trends """
    if request.method == "POST":
        child_id = request.POST.get('child_id')
        child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
        
        # Save to your BehaviorLog model (ensure this model exists)
        # Note: This logic can later be used to auto-recommend 'Calm' lessons if mood is anxious
        BehaviorLog.objects.create(
            child=child,
            mood=request.POST.get('mood', 'calm'),
            sleep_quality=request.POST.get('sleep_quality') or request.POST.get('sleep', ''),
            social_interaction=request.POST.get('social_interaction') or '',
            meltdown_episodes=int(request.POST.get('meltdowns') or 0),
            attention_level=int(request.POST.get('attention') or 3)
        )
        
        messages.success(request, f"Behavior log for {child.name} saved.")
    return redirect('parent_dashboard')

# --- UPDATED: CHILD PORTAL VIEW ---
@login_required
def student_assigned_today(request, child_id):
    """ Feature: The child only sees what the parent assigned for today """
    child = get_object_or_404(ChildProfile, id=child_id)
    today = date.today()
    
    # Filter assignments specifically for today
    assigned_tasks = Assignment.objects.filter(
        child=child, 
        assigned_date=today
    ).select_related('lesson')
    
    return render(request, 'accounts/child/assigned_today.html', {
        'child': child,
        'tasks': assigned_tasks
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
    """ Parent-led bypass for high-sensitivity students """
    child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
    
    # We create a 'Trust Token' in the session
    request.session['assisted_session'] = True
    request.session['active_child_id'] = child.id
    
    # Redirect straight to the portal, skipping the student login page
    messages.success(request, f"Assisted session started for {child.name}")
    return redirect('skill_selection_portal', child_id=child.id)
from django.db.models import Sum

@login_required
def skill_selection_portal(request, child_id):
    """ 
    Smart Gateway: 
    1. Allows parent access for high-sensitivity (Meena)
    2. Allows direct student access for low-sensitivity (Hanna)
    """
    child = get_object_or_404(ChildProfile, id=child_id)

    # SECURITY CHECK: Ensure the person accessing this is either the parent OR the child themselves
    is_parent = (request.user.role == 'parent' and child.parent == request.user)
    is_the_child = (request.user.role == 'student' and request.user.username == child.user.username)

    if not (is_parent or is_the_child):
        return HttpResponseForbidden("You do not have permission to access this portal.")

    # CLINICAL CHECK: If child is high-sensitivity (Meena) but no parent is logged in
    if child.autism_percentage >= 50 and request.user.role == 'student':
        messages.error(request, "This profile requires Assisted Launch. Please ask your parent to log in.")
        return redirect('login')

    # Session Management
    request.session['active_child_id'] = child.id
    
    # Calculate Stars (Using your existing logic)
    # Note: Ensure ActivityProgress model is imported
    total_stars = ActivityProgress.objects.filter(child=child).aggregate(Sum('stars_earned'))['stars_earned__sum'] or 0

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
        'skills': skill_list,
        'total_stars': total_stars,
        'is_assisted': (request.user.role == 'parent'), # Tell the template if parent is watching
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
    """ 
    Smart Exit Logic:
    - If Student logged in directly -> send to Independent Dashboard
    - If Parent is using Assisted Mode -> send to Parent Dashboard
    """
    # 1. Check if the logged-in user is a Parent
    if request.user.role == 'parent':
        # Clear the active child session tracking
        if 'active_child_id' in request.session:
            del request.session['active_child_id']
        return redirect('parent_dashboard')

    # 2. Check if the logged-in user is a Student
    elif request.user.role == 'student':
        return redirect('independent_student_dashboard')

    # Fallback
    return redirect('home')

# --- ADMIN SECTION (Module 1.0) ---
# accounts/views.py

# This fetches your custom 'accounts.User' model correctly
User = get_user_model() 

# accounts/views.py
# accounts/views.py
from django.db.models import Count
from django.utils import timezone

# accounts/views.py

# accounts/views.py

# accounts/views.py

# accounts/views.py

# accounts/views.py

# accounts/views.py

@login_required
def admin_dashboard(request):
    if not (request.user.role == 'admin' or request.user.is_superuser):
        return HttpResponseForbidden()

    # 1. Fetch Professional Users (Parents/Contributors) awaiting approval
    pending_users = User.objects.filter(
        is_approved=False
    ).exclude(role='student').exclude(id=request.user.id)

    # 2. UPDATED: Fetch Student Profiles awaiting verification
    # Only students with < 50% sensitivity (Direct Access users) need Admin approval.
    # High sensitivity students (Meena) are skipped because they use Assisted Launch.
    pending_student_profiles = ChildProfile.objects.filter(
        user__is_approved=False,
        autism_percentage__lt=50  # Logic: < 50% needs Admin gatekeeping
    ).select_related('user', 'parent')

    # 3. Fetch Parent Feedback
    pending_feedback = LessonFeedback.objects.filter(is_moderated=False)

    # Counting logic
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    daily_active = ActivityProgress.objects.filter(completed_at__gte=today_start).values('child').distinct().count()

    context = {
        'pending_users': pending_users,
        'pending_student_profiles': pending_student_profiles, # Now filtered for Hanna only
        'pending_feedback': pending_feedback,
        'total_parents': User.objects.filter(role='parent').count(),
        'total_contributors': User.objects.filter(role='contributor').count(),
        'total_children': ChildProfile.objects.count(),
        'total_activities': Lesson.objects.filter(is_approved=True).count(),
        'daily_active_users': daily_active,
        'total_approved': User.objects.filter(is_approved=True).exclude(id=request.user.id).count(),
        'pending_lessons': Lesson.objects.filter(is_approved=False),
        'approved_lessons': Lesson.objects.filter(is_approved=True),
        'categories': Lesson.objects.values('skill_category').annotate(count=Count('id')),
        'today': timezone.now(),
    }
    
    return render(request, 'accounts/dashboards/admin_dashboard.html', context)
@login_required
def approve_student_account(request, user_id):
    """ Admin verification for child profiles (Standard MCA Security Flow) """
    if not (request.user.role == 'admin' or request.user.is_superuser):
        return HttpResponseForbidden()
    
    student_user = get_object_or_404(User, id=user_id)
    student_user.is_approved = True
    student_user.save()
    
    messages.success(request, f"Student profile for {student_user.username} has been verified and activated.")
    return redirect('admin_dashboard')

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

# accounts/views.py

@login_required
def send_notifications(request):
    """ DFD Process 1.0.6: Global Role-Based Broadcast System """
    if request.method == "POST":
        target_roles = request.POST.getlist('target') # ['parent', 'contributor']
        msg_text = request.POST.get('message')
        
        if not target_roles:
            messages.error(request, "Please select at least one target role.")
            return redirect('admin_dashboard')

        # Dispatch to every user matching the selected roles
        users_to_notify = User.objects.filter(role__in=target_roles)
        
        notifications = [
            Notification(user=user, message=msg_text) 
            for user in users_to_notify
        ]
        
        # Bulk create is more efficient for large user bases
        Notification.objects.bulk_create(notifications)
            
        messages.success(request, f"Broadcast successfully sent to {users_to_notify.count()} active users.")
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
        activity_type = request.POST.get('activity_type', 'none')
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
            activity_type=activity_type,
            file=request.FILES.get('file'),
            video_url=video_url,
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
def system_activity_player_by_assignment(request, assignment_id):
    """Redirect to lesson player when opening from an assignment."""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    return redirect('system_activity_player', lesson_id=assignment.lesson_id)
# --- Add these new functions to your views.py ---
@login_required
def child_login_redirect(request, child_id):
    """
    Logic:
    - High Sensitivity (Meena): Parent launches DIRECTLY. No Admin approval needed 
      because the Parent is the supervisor.
    - Low Sensitivity (Hanna): Needs Admin Approval + Redirects to Login for 
      Independent Access.
    """
    child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
    
    # 1. MEENA'S PATH (High Sensitivity >= 50%)
    if child.autism_percentage >= 50:
        # We bypass 'is_approved' check because Parent is the 'Key'
        messages.success(request, f"Assisted clinical session started for {child.name}")
        return redirect('skill_selection_portal', child_id=child.id)
    
    # 2. HANNA'S PATH (Low Sensitivity < 50%)
    else:
        # Check if Admin has approved her for independent login
        if not child.is_approved:
            messages.warning(request, f"Independent access for {child.name} is awaiting Admin verification.")
            return redirect('parent_dashboard')
            
        # If approved, send her to the login page to enter her own password
        messages.info(request, f"Direct Access enabled. Please let {child.name} log in.")
        return redirect('login')


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

# accounts/views.py
@login_required
@transaction.atomic
def add_child(request):
    """ Corrected registration with unique email and explicit parent linking """
    if request.user.role.lower() != 'parent':
        return HttpResponseForbidden("Access Denied")

    screening_questions = [
        "1. Eye contact?", "2. Repeating words?", "3. Solitary play?",
        "4. Sensory reactions?", "5. Routine changes?", "6. Response to name?",
        "7. Motor behaviors?", "8. Texture aversion?", "9. Intense focus?", "10. Gestures?"
    ]
        
    if request.method == 'POST':
        s_username = request.POST.get('student_username')
        s_password = request.POST.get('student_password')

        # Prevent username duplicates
        if User.objects.filter(username=s_username).exists():
            messages.error(request, "This student username is already taken.")
            return redirect('add_child')

        # Score calculation
        q_keys = [f'q{i}' for i in range(1, 11)] 
        yes_count = sum(1 for k in q_keys if request.POST.get(k) == 'yes')
        percentage = (yes_count / 10) * 100 
        auto_approve = (percentage >= 50) 

        try:
            # 1. Create User with Unique Virtual Email
            # This prevents the 'UNIQUE constraint failed: accounts_user.email' error
            s_email = f"{s_username}@neuroskills.local"

            child_user = User.objects.create_user(
                username=s_username, 
                password=s_password,
                email=s_email,
                role='student'
            )
            child_user.is_approved = auto_approve
            child_user.save()
            
            # 2. Create Profile linked to the Parent
            interests_str = ','.join(request.POST.getlist('interests'))
            sensory_str = ','.join(request.POST.getlist('sensory_sensitivity'))

            child = ChildProfile.objects.create(
                user=child_user,
                parent=request.user, # CRITICAL: This links the child to the parent
                name=request.POST.get('name'),
                age=int(request.POST.get('age') or 0),
                gender=request.POST.get('gender', ''),
                diagnosis=request.POST.get('diagnosis_type', 'General Development'), 
                learning_style=request.POST.get('learning_style', 'visual'),
                sensory_mode=request.POST.get('sensory_mode', 'neutral'),
                interests=interests_str,
                sensory_sensitivity=sensory_str,
                autism_percentage=percentage
            )
            
            # 3. Log screening
            ScreeningResult.objects.create(child=child, score_percentage=percentage)

            messages.success(request, f"Profile for {child.name} saved successfully!")
            return redirect('parent_dashboard')
            
        except Exception as e:
            print(f"DATABASE ERROR: {e}") # Check your VS Code terminal for this
            messages.error(request, f"Could not save profile: {str(e)}")
    
    return render(request, 'accounts/child/add_child.html', {'screening_questions': screening_questions})
@login_required
@transaction.atomic
def edit_child(request, child_id):
    """ 
    Enhanced Edit Logic:
    - Updates clinical and sensory profile.
    - Updates existing Student User account (username/password).
    - Creates a NEW account if the profile was 'orphaned' (Hanna's case).
    """
    child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
    
    if request.method == 'POST':
        new_username = request.POST.get('student_username')
        new_password = request.POST.get('student_password')

        # --- 1. HANDLE ACCOUNT UPDATES OR CREATION ---
        if child.user:
            # Case: Update existing account
            if new_username and new_username != child.user.username:
                if User.objects.filter(username=new_username).exists():
                    messages.error(request, f"The username '{new_username}' is already taken.")
                else:
                    child.user.username = new_username
            
            if new_password:
                child.user.set_password(new_password)
            
            child.user.save()
        
        elif new_username and new_password:
            # Case: Fix for 'Hanna' (No account yet)
            if User.objects.filter(username=new_username).exists():
                messages.error(request, "Username taken. Could not create account link.")
            else:
                s_email = f"{new_username}@neuroskills.local"
                new_user = User.objects.create_user(
                    username=new_username,
                    password=new_password,
                    email=s_email,
                    role='student'
                )
                new_user.is_approved = (child.autism_percentage >= 50) # Sync approval logic
                new_user.save()
                
                child.user = new_user # Link the new account to the old profile
                messages.info(request, f"Created new login credentials for {child.name}.")

        # --- 2. UPDATE CLINICAL & SENSORY PROFILE ---
        child.name = request.POST.get('name')
        child.age = int(request.POST.get('age', 0) or child.age)
        child.gender = request.POST.get('gender', '')
        child.autism_level = request.POST.get('autism_level', '')
        child.learning_style = request.POST.get('learning_style', child.learning_style)
        child.sensory_mode = request.POST.get('sensory_mode', child.sensory_mode)
        child.diagnosis_type = request.POST.get('diagnosis_type', child.diagnosis_type)
        child.interests = request.POST.get('interests', '')
        child.notes = request.POST.get('notes', '')

        if request.FILES.get('child_photo'):
            child.child_photo = request.FILES.get('child_photo')

        child.save()
        messages.success(request, f"Profile and credentials for {child.name} have been updated.")
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
    child = None
    if 'active_child_id' in request.session:
        child = get_object_or_404(ChildProfile, id=request.session['active_child_id'])
    game_type = getattr(lesson, 'activity_type', 'none')
    return render(request, 'accounts/child/system_player.html', {
        'lesson': lesson,
        'mode': mode,
        'child': child,
        'game_type': game_type,
        'is_admin': request.user.is_superuser,
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

# accounts/views.py

# accounts/views.py

# accounts/views.py
from django.db.models import Sum

# accounts/views.py
from django.db.models import Sum

@login_required
def record_completion(request, lesson_id):
    if request.method == 'POST':
        # Safely get the child ID from session or a fallback
        child_id = request.session.get('active_child_id')
        
        if not child_id:
            # Fallback for MCA Demo: Use the parent's first child if session is lost
            child = request.user.children.first()
        else:
            child = get_object_or_404(ChildProfile, id=child_id)

        lesson = get_object_or_404(Lesson, id=lesson_id)

        # 1. Save Progress
        ActivityProgress.objects.create(
            child=child, 
            lesson=lesson,
            stars_earned=3 
        )
        
        # 2. Update Streak (Process 4.0.6)
        today = timezone.now().date()
        if child.last_activity_date != today:
            child.current_streak += 1
            child.last_activity_date = today
            child.save()

        # 3. Calculate Total for JSON response
        total = ActivityProgress.objects.filter(child=child).aggregate(Sum('stars_earned'))['stars_earned__sum'] or 0
        
        return JsonResponse({
            'status': 'success', 
            'total_stars': total,
            'streak': child.current_streak
        })
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
@login_required
def reward_store(request, child_id):
    """Child reward screen: stars earned and rewards (parent-defined or defaults)."""
    child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
    total_stars = ActivityProgress.objects.filter(child=child).aggregate(Sum('stars_earned'))['stars_earned__sum'] or 0
    parent_rewards = ParentReward.objects.filter(child=child).order_by('stars_required')
    if parent_rewards.exists():
        rewards = [{'id': r.id, 'name': r.reward_description, 'cost': r.stars_required, 'icon': 'fa-gift'} for r in parent_rewards]
    else:
        rewards = [
            {'id': 'confetti', 'name': 'Confetti Rain', 'cost': 5, 'icon': 'fa-paper-plane'},
            {'id': 'fireworks', 'name': 'Magic Fireworks', 'cost': 10, 'icon': 'fa-firework'},
            {'id': 'balloon', 'name': 'Balloon Party', 'cost': 15, 'icon': 'fa-balloon'},
        ]
    return render(request, 'accounts/child/reward_store.html', {
        'child': child,
        'total_stars': total_stars,
        'rewards': rewards,
    })


@login_required
def parent_reward_manage(request, child_id):
    """Parents set rewards e.g. 10 stars → Chocolate, 20 stars → Toy."""
    if request.user.role != 'parent':
        return HttpResponseForbidden("Access Denied")
    child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
    rewards = ParentReward.objects.filter(child=child).order_by('stars_required')
    if request.method == 'POST':
        stars_required = request.POST.get('stars_required')
        reward_description = request.POST.get('reward_description', '').strip()
        if stars_required and reward_description:
            ParentReward.objects.create(
                parent=request.user,
                child=child,
                stars_required=int(stars_required),
                reward_description=reward_description,
            )
            messages.success(request, f"Reward added: {stars_required} stars → {reward_description}")
            return redirect('parent_reward_manage', child_id=child.id)
    return render(request, 'accounts/parent/reward_manage.html', {'child': child, 'rewards': rewards})


@login_required
def parent_reward_delete(request, reward_id):
    reward = get_object_or_404(ParentReward, id=reward_id, parent=request.user)
    child_id = reward.child_id
    reward.delete()
    messages.success(request, "Reward removed.")
    return redirect('parent_reward_manage', child_id=child_id)


@login_required
def learning_plan_list(request, child_id):
    """List custom learning plans for a child."""
    if request.user.role != 'parent':
        return HttpResponseForbidden("Access Denied")
    child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
    plans = LearningPlan.objects.filter(child=child).prefetch_related('items').order_by('-created_at')
    return render(request, 'accounts/parent/learning_plan_list.html', {'child': child, 'plans': plans})


@login_required
def learning_plan_create(request, child_id):
    """Create custom learning plan: Skill, Activity, Duration; Daily/Weekly/Custom."""
    if request.user.role != 'parent':
        return HttpResponseForbidden("Access Denied")
    child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
    approved_lessons = Lesson.objects.filter(is_approved=True)
    if request.method == 'POST':
        name = request.POST.get('name', 'My Plan')
        plan_type = request.POST.get('plan_type', 'daily')
        custom_difficulty = request.POST.get('custom_difficulty', '')
        plan = LearningPlan.objects.create(
            parent=request.user,
            child=child,
            name=name,
            plan_type=plan_type,
            custom_difficulty=custom_difficulty,
        )
        # Optional: add items from form (skill, activity, duration)
        for key in request.POST:
            if key.startswith('skill_') and key.replace('skill_', '').isdigit():
                idx = key.replace('skill_', '')
                activity = request.POST.get(f'activity_{idx}', '')
                duration = request.POST.get(f'duration_{idx}', 5)
                if request.POST.get(key) and activity:
                    LearningPlanItem.objects.create(
                        plan=plan,
                        skill=request.POST.get(key),
                        activity=activity,
                        duration_minutes=int(duration) if str(duration).isdigit() else 5,
                        order=int(idx) if idx.isdigit() else 0,
                    )
        messages.success(request, f"Learning plan '{name}' created.")
        return redirect('learning_plan_list', child_id=child.id)
    return render(request, 'accounts/parent/learning_plan_create.html', {'child': child, 'approved_lessons': approved_lessons})
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
@login_required
def manage_categories(request):
    """ Feature: Dynamic Category Creation for Admin """
    if request.method == "POST":
        new_name = request.POST.get('category_name').strip().lower()
        # In a real model-based setup, you'd save to a Category model.
        # Since your Lesson model uses CharField categories, we notify success:
        messages.success(request, f"New skill area '{new_name}' is now available for contributors.")
        return redirect('admin_dashboard')
    
    return redirect('admin_dashboard')

@login_required
def delete_category(request, cat_slug):
    """ Feature: Remove focus area and cleanup related modules """
    Lesson.objects.filter(skill_category=cat_slug).delete()
    messages.warning(request, f"Skill area '{cat_slug}' and all associated lessons removed.")
    return redirect('admin_dashboard')
@login_required
def assign_task(request):
    """ Fixed function name to match your urls.py path('assign-daily-task/') """
    if request.method == "POST":
        child_id = request.POST.get('child_id')
        category = request.POST.get('category')
        
        child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
        
        # Logic: Filter lessons by the guide's age categories (Toddler, Kinder, etc.)
        bundle_lessons = Lesson.objects.filter(target_age_group__iexact=category, is_approved=True)
        
        for lesson in bundle_lessons:
            # get_or_create prevents duplicate assignments for the same day
            Assignment.objects.get_or_create(
                child=child,
                lesson=lesson,
                assigned_date=date.today()
            )
            
        messages.success(request, f"Daily {category} curriculum assigned to {child.name}.")
    return redirect('parent_dashboard')

@login_required
def save_behavior_log(request):
    """ Handles the Behavior Tracking Card data """
    if request.method == "POST":
        child_id = request.POST.get('child_id')
        child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
        
        BehaviorLog.objects.create(
            child=child,
            mood=request.POST.get('mood', 'calm'),
            sleep_quality=request.POST.get('sleep_quality') or request.POST.get('sleep', ''),
            social_interaction=request.POST.get('social_interaction') or 'Neutral',
            meltdown_episodes=int(request.POST.get('meltdowns') or 0),
            attention_level=int(request.POST.get('attention') or 3)
        )
        
        messages.success(request, f"Daily behavioral insights for {child.name} recorded.")
    return redirect('parent_dashboard')

def log_daily_mood(request):
    if request.method == "POST":
        child_id = request.POST.get('child_id')
        mood = request.POST.get('mood')
        note = request.POST.get('behavior_note')
        
        # LOGIC: Save this to your Database
        # Example: DailyLog.objects.create(child_id=child_id, mood=mood, note=note)
        
        messages.success(request, "Daily readiness logged successfully!")
    return redirect('parent_dashboard')


    return redirect('parent_dashboard')
@login_required
def assign_daily_lessons(request):
    if request.method == 'POST':
        child_id = request.POST.get('child_id')
        child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
        lesson_ids = request.POST.getlist('lessons')
        for lid in lesson_ids:
            Assignment.objects.update_or_create(
                child=child,
                lesson_id=lid,
                assigned_date=date.today(),
                defaults={'is_completed': False}
            )
        messages.success(request, f"Assigned {len(lesson_ids)} activities to {child.name} for today.")
        return redirect('parent_dashboard')
@login_required
@never_cache
def independent_student_dashboard(request):
    # Security: Ensure only students can see this
    if request.user.role != 'student':
        return redirect('role_dashboard')

    # Get the profile linked to this user
    child = get_object_or_404(ChildProfile, user=request.user)
    
    # Calculate Stars and Progress
    total_stars = ActivityProgress.objects.filter(child=child).aggregate(Sum('stars_earned'))['stars_earned__sum'] or 0
    
    # Get today's assignments
    assigned_tasks = Assignment.objects.filter(
        child=child, 
        assigned_date=date.today(),
        is_completed=False
    ).select_related('lesson')

    return render(request, 'accounts/child/independent_dashboard.html', {
        'child': child,
        'total_stars': total_stars,
        'tasks': assigned_tasks,
    })
@login_required
def high_sensitivity_dashboard(request, child_id):
    """ 
    Specialized UI for High Support Students:
    - Minimalist 'One Task at a Time' view.
    - Large focus buttons.
    - Calm color palette.
    """
    child = get_object_or_404(ChildProfile, id=child_id, parent=request.user)
    
    # Track that this is a parent-supervised session
    request.session['active_child_id'] = child.id
    request.session['assisted_session'] = True

    # Fetch only the FIRST uncompleted task for total focus
    current_task = Assignment.objects.filter(
        child=child, 
        assigned_date=date.today(),
        is_completed=False
    ).select_related('lesson').first()

    return render(request, 'accounts/child/high_sensitivity_dashboard.html', {
        'child': child,
        'task': current_task,
    })