from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class User(AbstractUser):
    ROLE_CHOICES = (
        ('parent', 'Parent'), 
        ('contributor', 'Contributor'), 
        ('admin', 'Admin')
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    email = models.EmailField(unique=True)
    
    # Feature: Admin Moderation of Registrations
    is_approved = models.BooleanField(default=False) 

    REQUIRED_FIELDS = ['email', 'phone', 'role']

    def __str__(self):
        return f"{self.username} ({self.role}) | Approved: {self.is_approved}"

class ChildProfile(models.Model):
    parent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='children'
    )
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    
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
    diagnosis = models.CharField(max_length=150, blank=True, verbose_name="Primary Focus Area")
    notes = models.TextField(blank=True, verbose_name="Sensory Triggers or Notes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # ... keep your existing fields (parent, name, age, etc.) ...
    
    # New fields for the one-time screening logic
    autism_percentage = models.FloatField(default=0.0)
    is_high_sensitivity = models.BooleanField(default=False)
    
    # ... keep your existing __str__ method ...

    def __str__(self):
        return f"{self.name} ({self.parent.email})"

# accounts/models.py
import urllib.parse as urlparse
from django.db import models

class Lesson(models.Model):
    # Existing fields
    contributor = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    is_activity = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True, null=True) # Logic: Admin writes notes here on rejection
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
class Assignment(models.Model):
    child = models.ForeignKey(ChildProfile, on_delete=models.CASCADE, related_name='assignments')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    assigned_date = models.DateField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    
    # Personalization logic from Parent Gateway
    target_mood = models.CharField(max_length=50, blank=True) 
    iq_focus = models.CharField(max_length=50, blank=True)   

    def __str__(self):
        return f"{self.lesson.title} for {self.child.name}"

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
        return f"Feedback for {lesson.title} by {parent.first_name}"
