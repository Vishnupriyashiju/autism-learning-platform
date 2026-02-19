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

    def __str__(self):
        return f"{self.name} ({self.parent.email})"

class Lesson(models.Model):
    contributor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    skill_category = models.CharField(max_length=50, default='communication')
    difficulty_level = models.CharField(max_length=20, default='beginner')
    
    # Media & Activity Engines
    MEDIA_TYPES = (
        ('video', 'Video Lesson'),
        ('audio', 'Audio/Sound Clip'),
        ('animation', 'Animated Content'),
        ('image_set', 'Image Set'),
    )
    content_type = models.CharField(max_length=20, choices=MEDIA_TYPES)
    
    ACTIVITY_TYPES = (
        ('none', 'General Lesson (No Game)'),
        ('matching', 'Matching Game'),
        ('sequencing', 'Sequencing Task'),
        ('shuffling', 'Card Shuffling'),
        ('drag_drop', 'Drag and Drop'),
    )
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES, default='none')
    
    file = models.FileField(upload_to='contributor_content/')
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True)
    
    # Content Moderation
    is_approved = models.BooleanField(default=False)
    admin_feedback = models.TextField(blank=True, null=True)
    
    # Performance Insights
    views_count = models.PositiveIntegerField(default=0)
    completion_rate = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.get_content_type_display()})"

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
class Notification(models.Model):
    message = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Global Alert: {self.message[:30]}..."