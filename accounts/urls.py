from django.urls import path
from . import views

urlpatterns = [
    # --- AUTHENTICATION & CORE ---
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.role_dashboard, name='role_dashboard'),

    # --- PARENT DASHBOARD & CHILD MANAGEMENT ---
    path('dashboard/parent/', views.parent_dashboard, name='parent_dashboard'),
    path('dashboard/parent/children/', views.child_list, name='child_list'),
    path('dashboard/parent/children/add/', views.add_child, name='add_child'),
    
    # Feature: Autism Readiness Screening (Process 2.0.4)
    path('dashboard/parent/screening/<int:child_id>/', views.child_screening_test, name='child_screening_test'),
    
    # Feature: Personalization Gate (Mood/IQ Assessment)
    path('dashboard/parent/launch-gate/<int:child_id>/', views.launch_child_gate, name='launch_child_gate'),

    # --- THE SENSORY PORTAL (FULL-PAGE SKILL SELECTION) ---
    # Feature: Full-page Skill Selection Grid (Process 4.0.6)
    path('dashboard/parent/skill-portal/<int:child_id>/', views.skill_selection_portal, name='skill_selection_portal'),
    
    # Feature: Skill-Specific Lesson Filtering (Process 4.0.1)
    path('dashboard/parent/skill-lessons/<int:child_id>/<str:skill_slug>/', views.skill_lessons_view, name='skill_lessons_view'),

    # --- CHILD LEARNING INTERFACE ---
    path('dashboard/child/<int:child_id>/', views.child_dashboard, name='child_dashboard'),
    path('activity/play/<int:assignment_id>/', views.system_activity_player, name='system_activity_player'),
    path('activity/complete/<int:assignment_id>/', views.complete_activity, name='complete_activity'),
    path('dashboard/child/exit/', views.exit_child_gate, name='exit_child_gate'),

    # --- CONTRIBUTOR DASHBOARD ---
    path('dashboard/contributor/', views.contributor_dashboard, name='contributor_dashboard'),
    path('dashboard/contributor/upload/', views.upload_lesson, name='upload_lesson'),

    # --- ADMIN COMMAND CENTER (Module 1.0) ---
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    
    # DFD Process 1.0.1 & 1.0.2
    path('dashboard/admin/categories/', views.manage_categories, name='manage_categories'),
    path('dashboard/admin/difficulty/', views.manage_difficulty, name='manage_difficulty'),
    
    # DFD Process 1.0.5 & 1.0.6
    path('dashboard/admin/analytics/', views.view_analytics, name='view_analytics'),
    path('dashboard/admin/notifications/', views.send_notifications, name='send_notifications'),
    
    # DFD Process 1.0.4
    path('dashboard/admin/config/', views.platform_config, name='platform_config'),
    
    # Admin User & Content Moderation
    path('dashboard/admin/approve/<int:user_id>/', views.approve_user, name='approve_user'),
    path('dashboard/admin/reject/<int:user_id>/', views.reject_user, name='reject_user'),
    path('dashboard/admin/approve-lesson/<int:lesson_id>/', views.approve_lesson, name='approve_lesson'),
]