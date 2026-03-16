from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = (
        ('parent', 'Parent'), 
        ('contributor', 'Contributor'), 
        ('admin', 'Admin'),
        ('student', 'Student'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    email = models.EmailField(unique=True)
    is_approved = models.BooleanField(default=False) 
    profile_photo = models.ImageField(upload_to='profiles/', null=True, blank=True)
    # NEW: Professional Fields for Contributors
    qualification = models.CharField(max_length=255, blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    specialization = models.CharField(max_length=100, blank=True)
    certificate = models.FileField(upload_to='certificates/', null=True, blank=True)
    portfolio_url = models.URLField(blank=True)
    location = models.CharField(max_length=255, blank=True)  # Country / Location
    # Parent-specific
    relationship_to_child = models.CharField(max_length=50, blank=True)  # Mother, Father, Guardian
    # Consent (Parent registration)
    data_privacy_agreed = models.BooleanField(default=False)
    progress_tracking_permission = models.BooleanField(default=False)

    REQUIRED_FIELDS = ['email', 'phone', 'role']

    def __str__(self):
        return f"{self.username} ({self.role}) | Approved: {self.is_approved}"

class ChildProfile(models.Model):
    # CRITICAL: Links the profile to the student's unique login account
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='child_profile',
        null=True, # Allow null for old records
        blank=True
    )
    parent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='children'
    )
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    current_streak = models.PositiveIntegerField(
        default=0, 
        help_text="Consecutive days of activity"
    )
    last_activity_date = models.DateField(
        null=True, 
        blank=True,
        help_text="The last date a lesson was completed"
    )
    # Sensory-Friendly UI Functionality
    LEARNING_STYLES = (
        ('visual', 'Visual (Images/Videos)'),
        ('audio', 'Auditory (Sound/Music)'),
        ('kinesthetic', 'Activity-based (Interactive)'),
    )
    learning_style = models.CharField(max_length=20, choices=LEARNING_STYLES, default='visual')

    SENSORY_MODES = (
        ('low', 'Low Stimulation (Calm/Minimal)'),
        ('high', 'High Engagement (Vibrant/Active)'),
        ('neutral', 'Standard Mode'),
    )
    sensory_mode = models.CharField(max_length=20, choices=SENSORY_MODES, default='neutral')

    reward_preference = models.CharField(max_length=20, default='stars')
    diagnosis = models.CharField(max_length=150, blank=True, null=True, verbose_name="Primary Focus Area")   
    notes = models.TextField(blank=True, verbose_name="Sensory Triggers or Notes")
    
    # Screening Logic
    autism_percentage = models.FloatField(default=0.0)
    is_high_sensitivity = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    relationship_to_child = models.CharField(max_length=50, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    autism_level = models.CharField(max_length=50, blank=True) # Mild, Moderate, Severe
    diagnosis_type = models.CharField(max_length=50, blank=True) # Autism, ADHD, Both
    
    # Learning Preferences: interests (Animals, Numbers, etc.), sensory_sensitivity (Sound/Light/Touch)
    interests = models.TextField(blank=True, help_text="Comma separated: Animals, Numbers, Music, Colors, Stories")
    sensory_sensitivity = models.TextField(blank=True)
    child_photo = models.ImageField(upload_to='child_photos/', null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.parent.email})"

# accounts/models.py
import urllib.parse as urlparse
from django.db import models

class Lesson(models.Model):
    ACTIVITY_TYPE_CHOICES = (
        ('none', 'General Lesson (No Game)'),
        ('matching', 'Matching Game'),
        ('sequencing', 'Sequencing Task'),
        ('emotion', 'Emotion Recognition'),
        ('memory', 'Memory Game'),
        ('drag_drop', 'Drag and Drop'),
    )
    contributor = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    is_activity = models.BooleanField(default=False)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES, default='none')
    admin_notes = models.TextField(blank=True, null=True)
    # Professional Metadata
    duration_minutes = models.IntegerField(default=0)
    skill_category = models.CharField(max_length=100)
    target_age_group = models.CharField(max_length=50)
    difficulty_level = models.CharField(max_length=50)
    learning_objectives = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    content_type = models.CharField(max_length=50) # 'video', 'pdf', 'youtube', etc.
    
    # Assets
    file = models.FileField(upload_to='lessons/files/', blank=True, null=True) # Set blank=True if using URL instead
    thumbnail = models.ImageField(upload_to='lessons/thumbs/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True, help_text="Paste YouTube link here")
    
    # Control
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def youtube_id(self):
        """Extracts the YouTube ID from various URL formats"""
        if not self.video_url:
            return None
        
        parsed_url = urlparse.urlparse(self.video_url)
        if parsed_url.hostname == 'youtu.be':
            return parsed_url.path[1:]
        if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
            if parsed_url.path == '/watch':
                return urlparse.parse_qs(parsed_url.query).get('v', [None])[0]
            if parsed_url.path[:7] == '/embed/':
                return parsed_url.path.split('/')[2]
            if parsed_url.path[:3] == '/v/':
                return parsed_url.path.split('/')[2]
        return None

    def __str__(self):
        return self.title


# Feature: Professional Screening Gate for Autism Percentage Calculation
class ScreeningResult(models.Model):
    child = models.ForeignKey(ChildProfile, on_delete=models.CASCADE, related_name='screening_tests')
    score_percentage = models.FloatField()
    is_high_sensitivity = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Test for {self.child.name}: {self.score_percentage}%"

# Feature: Global System Notifications
# accounts/models.py

class Notification(models.Model):
    # ADD THIS LINE: Links the notification to a specific user
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    message = models.TextField()
    is_active = models.BooleanField(default=True)
    is_read = models.BooleanField(default=False) # Good for demo tracking
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        recipient = self.user.username if self.user else "Global"
        return f"Alert for {recipient}: {self.message[:30]}..."
# accounts/models.py
class ActivityProgress(models.Model):
    child = models.ForeignKey(ChildProfile, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)
    stars_earned = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.child.name} - {self.lesson.title}"
# accounts/models.py
class LessonFeedback(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='user_feedback')
    parent = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_moderated = models.BooleanField(default=False) # Admin must check this
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.lesson.title} by {self.parent.first_name}"

class BehaviorLog(models.Model):
    MOOD_CHOICES = [
        ('calm', 'Calm'), ('energetic', 'Energetic'), ('anxious', 'Anxious'), ('tired', 'Tired'),
        ('Happy', 'Happy'), ('Anxious', 'Anxious'), ('Irritable', 'Irritable'),
    ]
    child = models.ForeignKey(ChildProfile, on_delete=models.CASCADE, related_name='behavior_logs')
    date = models.DateField(default=timezone.now)
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES)
    sleep_quality = models.CharField(max_length=20)
    social_interaction = models.CharField(max_length=50, blank=True, null=True)    
    meltdown_episodes = models.IntegerField(default=0)
    attention_level = models.IntegerField(default=3)

    def __str__(self):
        return f"{self.child.name} - {self.date}"

class Assignment(models.Model):
    child = models.ForeignKey(ChildProfile, on_delete=models.CASCADE, related_name='assignments')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    assigned_date = models.DateField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    target_mood = models.CharField(max_length=50, blank=True)
    class Meta:
        unique_together = ('child', 'lesson', 'assigned_date')


class ParentReward(models.Model):
    """Reward system: e.g. 10 stars → Chocolate, 20 stars → Toy."""
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rewards')
    child = models.ForeignKey(ChildProfile, on_delete=models.CASCADE, related_name='rewards')
    stars_required = models.PositiveIntegerField()
    reward_description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['stars_required']

    def __str__(self):
        return f"{self.child.name}: {self.stars_required} stars → {self.reward_description}"


class LearningPlan(models.Model):
    """Custom learning plan: daily, weekly, or custom."""
    PLAN_TYPES = (('daily', 'Daily'), ('weekly', 'Weekly'), ('custom', 'Custom'))
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_plans')
    child = models.ForeignKey(ChildProfile, on_delete=models.CASCADE, related_name='learning_plans')
    name = models.CharField(max_length=100, default='My Plan')
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, default='daily')
    custom_difficulty = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.child.name} - {self.get_plan_type_display()}"


class LearningPlanItem(models.Model):
    """Single row: Skill, Activity, Duration (e.g. Eye Contact, Look at cartoon, 5 min)."""
    plan = models.ForeignKey(LearningPlan, on_delete=models.CASCADE, related_name='items')
    skill = models.CharField(max_length=100)
    activity = models.CharField(max_length=255)
    duration_minutes = models.PositiveIntegerField(default=5)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.skill}: {self.activity} ({self.duration_minutes} min)"
