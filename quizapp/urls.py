from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('login', views.login_view, name='login'),
    path('register', views.register_view, name='register'),
    path('logout', views.logout_view, name='logout'),
    path('domain', views.domain, name='domain'),
    path('quiz/<str:domain>/<int:count>', views.quiz, name='quiz'),
    path('submit', views.submit_quiz, name='submit_quiz'),
    path('interview', views.interview, name='interview'),
    path('interview_finish', views.interview_finish, name='interview_finish'),
    path('download-interview-report', views.download_interview_report, name='download_interview_report'),
    path('resume', views.resume, name='resume'),
    path('download-pdf', views.download_pdf, name='download_pdf'),
    path('progress', views.progress, name='progress'),
]
