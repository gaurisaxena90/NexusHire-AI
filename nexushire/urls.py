from django.contrib import admin
from django.urls import path
from portal import views  # Humne jo views banaye the, unhe import kar rahe hain
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),  # Blank path matlab main home page
    path('login/', views.login_page, name='login'),
    path('register/', views.register_page, name='register'),
    path('hr-dashboard/', views.hr_dashboard, name='hr_dashboard'),
    path('candidate-dashboard/', views.candidate_dashboard, name='candidate_dashboard'),
    path('logout/', views.logout_user, name='logout'),
    path('delete-job/<int:job_id>/', views.delete_job, name='delete_job'),
    path('edit-job/<int:job_id>/', views.edit_job, name='edit_job'),
    path('apply-job/<int:job_id>/', views.apply_job, name='apply_job'),
    path('update-status/<int:app_id>/<str:status>/', views.update_status, name='update_status'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)