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
# Feature: Unified Activity Player (Supports: view, matching, shuffling, sequencing, drag_drop)
path('activity/play/<int:lesson_id>/', views.system_activity_player, name='system_activity_player'),

# Finalizing tasks and exiting
path('activity/complete/<int:assignment_id>/', views.complete_activity, name='complete_activity'),
path('dashboard/child/exit/', views.exit_child_gate, name='exit_child_gate'),

# Path for High-Sensitivity Student Login
path('student/portal/<int:child_id>/', views.student_login_view, name='student_login_page'),

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
    # ADD THIS LINE to fix the NoReverseMatch error
    path('dashboard/parent/redirect/<int:child_id>/', views.child_login_redirect, name='child_login_redirect'),
    
    # Path for the High-Sensitivity Student Login (if percentage >= 50)
    path('student/login/', views.student_login_view, name='student_login'),
    path('child/edit/<int:child_id>/', views.edit_child, name='edit_child'),
    path('child/remove/<int:child_id>/', views.remove_child, name='remove_child'),
    path('child/feedback/<int:child_id>/', views.save_parent_feedback, name='save_parent_feedback'),
    path('child/<int:child_id>/report/', views.parent_report_view, name='parent_report'),
    path('child/<int:child_id>/report/download/', views.download_progress_report, name='download_report'),
    path('activity/complete/<int:lesson_id>/', views.record_completion, name='record_completion'),
    path('child/<int:child_id>/report/', views.parent_report_view, name='parent_report'),
    path('feedback/submit/', views.submit_lesson_feedback, name='submit_lesson_feedback'),
    path('feedback/relay/<int:feedback_id>/', views.relay_feedback_to_contributor, name='relay_feedback_to_contributor'),
    path('skill-lessons/<slug:category_slug>/', views.skill_lessons_view, name='skill_lessons'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('request-update/<int:lesson_id>/', views.request_module_update, name='request_module_update'),
    path('dashboard/admin/delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('delete-module/<int:lesson_id>/', views.delete_module, name='delete_module'),
    path('dashboard/contributor/edit/<int:lesson_id>/', views.edit_lesson, name='edit_lesson'),
]