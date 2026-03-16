from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # --- AUTHENTICATION & CORE ---
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.role_dashboard, name='role_dashboard'),

    # --- PASSWORD RESET ---
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='accounts/password/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password/password_reset_complete.html'), name='password_reset_complete'),
    path('dashboard/student/portal/', views.independent_student_dashboard, name='independent_student_dashboard'),
    # --- PARENT DASHBOARD & CHILD MANAGEMENT ---
    path('dashboard/parent/', views.parent_dashboard, name='parent_dashboard'),
    path('dashboard/parent/children/', views.child_list, name='child_list'),
    path('dashboard/parent/children/add/', views.add_child, name='add_child'),
    path('dashboard/parent/screening/<int:child_id>/', views.child_screening_test, name='child_screening_test'),
    path('dashboard/parent/launch-gate/<int:child_id>/', views.launch_child_gate, name='launch_child_gate'),
    path('child/edit/<int:child_id>/', views.edit_child, name='edit_child'),
    path('child/remove/<int:child_id>/', views.remove_child, name='remove_child'),
    path('child/feedback/<int:child_id>/', views.save_parent_feedback, name='save_parent_feedback'),
    
    # --- PORTAL & LEARNING ---
    path('dashboard/parent/skill-portal/<int:child_id>/', views.skill_selection_portal, name='skill_selection_portal'),
    path('dashboard/parent/skill-lessons/<int:child_id>/<str:skill_slug>/', views.skill_lessons_view, name='skill_lessons_view'),
    path('dashboard/parent/skill-portal/<int:child_id>/rewards/', views.reward_store, name='reward_store'),
    path('dashboard/parent/child/<int:child_id>/rewards/', views.parent_reward_manage, name='parent_reward_manage'),
    path('dashboard/parent/reward/<int:reward_id>/delete/', views.parent_reward_delete, name='parent_reward_delete'),
    path('dashboard/parent/child/<int:child_id>/learning-plans/', views.learning_plan_list, name='learning_plan_list'),
    path('dashboard/parent/child/<int:child_id>/learning-plan/create/', views.learning_plan_create, name='learning_plan_create'),
    path('activity/play/<int:lesson_id>/', views.system_activity_player, name='system_activity_player'),
    path('activity/complete/<int:lesson_id>/', views.record_completion, name='record_completion'),
    path('dashboard/child/exit/', views.exit_child_gate, name='exit_child_gate'),
    path('dashboard/parent/redirect/<int:child_id>/', views.child_login_redirect, name='child_login_redirect'),

    # --- REPORTS & FEEDBACK ---
    path('child/<int:child_id>/report/', views.parent_report_view, name='parent_report'),
    path('child/<int:child_id>/report/download/', views.download_progress_report, name='download_report'),
    path('feedback/submit/', views.submit_lesson_feedback, name='submit_lesson_feedback'),
    
    # accounts/urls.py

# Replace lines 46-47 and 102 with these:
    path('log-mood/', views.save_behavior_log, name='save_behavior_log'),
    path('assign-lessons/', views.assign_daily_lessons, name='assign_daily_lessons'),

    # --- CONTRIBUTOR DASHBOARD ---
    path('dashboard/contributor/', views.contributor_dashboard, name='contributor_dashboard'),
    path('dashboard/contributor/upload/', views.upload_lesson, name='upload_lesson'),
    path('dashboard/contributor/edit/<int:lesson_id>/', views.edit_lesson, name='edit_lesson'),

    # --- ADMIN COMMAND CENTER ---
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/admin/skills/<str:skill_slug>/', views.skill_lessons_view, {'child_id': None}, name='skill_lessons'),
    path('dashboard/admin/analytics/', views.view_analytics, name='view_analytics'),
    path('dashboard/admin/notifications/', views.send_notifications, name='send_notifications'),
    path('dashboard/admin/config/', views.platform_config, name='platform_config'),
    path('dashboard/admin/approve/<int:user_id>/', views.approve_user, name='approve_user'),
    path('dashboard/admin/reject/<int:user_id>/', views.reject_user, name='reject_user'),
    path('dashboard/admin/approve-lesson/<int:lesson_id>/', views.approve_lesson, name='approve_lesson'),
    path('dashboard/admin/approve-student/<int:user_id>/', views.approve_student_account, name='approve_student'),    path('feedback/relay/<int:feedback_id>/', views.relay_feedback_to_contributor, name='relay_feedback_to_contributor'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('delete-module/<int:lesson_id>/', views.delete_module, name='delete_module'),
    path('request-update/<int:lesson_id>/', views.request_module_update, name='request_module_update'),
    path('dashboard/admin/skills/add/', views.manage_categories, name='manage_categories'),
    path('dashboard/admin/skills/delete/<str:cat_slug>/', views.delete_category, name='delete_category'),
    path('dashboard/child/high-support/<int:child_id>/', views.high_sensitivity_dashboard, name='high_sensitivity_dashboard'),
]