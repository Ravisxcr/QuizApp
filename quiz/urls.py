from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    
    # Book and Chapter Management
    path('add-book/', views.add_book, name='add_book'),
    path('add-chapter/', views.add_chapter, name='add_chapter'),
    path('books/', views.books_list, name='books_list'),
    
    # Question Management
    path('upload-questions/', views.upload_questions, name='upload_questions'),
    path('chapter/<int:chapter_id>/questions/', views.chapter_questions, name='chapter_questions'),
    
    # Quiz functionality
    path('quiz/', views.quiz_list, name='quiz_list'),
    path('quiz/start/chapter/<int:chapter_id>/', views.start_quiz, name='start_quiz'),
    path('quiz/start/book/<int:book_id>/', views.start_book_quiz, name='start_book_quiz'),
    path('quiz/take/<int:quiz_id>/', views.take_quiz, name='take_quiz'),
    path('quiz/results/<int:quiz_id>/', views.quiz_results, name='quiz_results'),
    path('quiz/history/', views.quiz_history, name='quiz_history'),
    
    # Authentication
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
]