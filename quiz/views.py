from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
import random
import json

from .models import Book, Chapter, Question, Quiz, QuizAnswer, QuizQuestionStatus
from .forms import BookForm, ChapterForm, QuestionUploadForm, QuizSelectionForm


def get_questions_for_source(source, difficulty='all'):
    """Helper function to get questions from either a chapter or book"""
    if isinstance(source, Chapter):
        questions_qs = source.questions.all()
    elif isinstance(source, Book):
        # Get questions from all chapters in the book
        questions_qs = Question.objects.filter(chapter__book=source)
    else:
        return Question.objects.none()
    
    if difficulty != 'all':
        questions_qs = questions_qs.filter(difficulty=difficulty)
    
    return questions_qs


def home(request):
    """Home page with navigation options"""
    total_books = Book.objects.count()
    total_chapters = Chapter.objects.count()
    total_questions = Question.objects.count()
    
    context = {
        'total_books': total_books,
        'total_chapters': total_chapters,
        'total_questions': total_questions,
    }
    return render(request, 'quiz/home.html', context)


def add_book(request):
    """Add a new book"""
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Book "{book.title}" has been added successfully!')
            return redirect('quiz:add_book')
    else:
        form = BookForm()
    
    books = Book.objects.all().order_by('-created_at')
    return render(request, 'quiz/add_book.html', {'form': form, 'books': books})


def add_chapter(request):
    """Add a new chapter"""
    if request.method == 'POST':
        form = ChapterForm(request.POST)
        if form.is_valid():
            chapter = form.save()
            messages.success(request, f'Chapter "{chapter.title}" has been added successfully!')
            return redirect('quiz:add_chapter')
    else:
        form = ChapterForm()
    
    chapters = Chapter.objects.select_related('book').order_by('-created_at')
    return render(request, 'quiz/add_chapter.html', {'form': form, 'chapters': chapters})


def upload_questions(request):
    """Upload questions via JSON"""
    if request.method == 'POST':
        form = QuestionUploadForm(request.POST)
        if form.is_valid():
            chapter = form.cleaned_data['chapter']
            questions_data = form.cleaned_data['questions_json']
            
            created_count = 0
            for question_data in questions_data:
                Question.objects.create(
                    chapter=chapter,
                    question_text=question_data['question_text'],
                    options=question_data.get('options', {}),
                    correct_answer=question_data['correct_answer'],
                    explanation=question_data.get('explanation', ''),
                    difficulty=question_data.get('difficulty', 'medium')
                )
                created_count += 1
            
            messages.success(request, f'{created_count} questions have been added to "{chapter.title}"!')
            return redirect('quiz:upload_questions')
    else:
        form = QuestionUploadForm()
    
    return render(request, 'quiz/upload_questions.html', {'form': form})


@login_required
def quiz_list(request):
    """List available quizzes"""
    chapters_with_questions = Chapter.objects.filter(questions__isnull=False).distinct().select_related('book')
    books_with_questions = Book.objects.filter(chapters__questions__isnull=False).distinct().prefetch_related('chapters__questions')
    
    context = {
        'chapters': chapters_with_questions,
        'books': books_with_questions,
    }
    return render(request, 'quiz/quiz_list.html', context)


@login_required
def start_quiz(request, chapter_id):
    """Start a new chapter quiz"""
    chapter = get_object_or_404(Chapter, id=chapter_id)
    
    if request.method == 'POST':
        form = QuizSelectionForm(request.POST)
        form.fields['chapter'].queryset = Chapter.objects.filter(id=chapter_id)
        form.fields['chapter'].initial = chapter
        form.fields['quiz_type'].initial = 'chapter'
        
        if form.is_valid():
            num_questions = form.cleaned_data['num_questions']
            difficulty = form.cleaned_data['difficulty']
            duration_minutes = int(form.cleaned_data['duration_minutes'])
            
            # Get questions based on difficulty
            questions_qs = get_questions_for_source(chapter, difficulty)
            
            if questions_qs.count() < num_questions:
                # Calculate difficulty counts for error response
                all_questions = get_questions_for_source(chapter)
                easy_count = all_questions.filter(difficulty='easy').count()
                medium_count = all_questions.filter(difficulty='medium').count()
                hard_count = all_questions.filter(difficulty='hard').count()
                
                context = {
                    'form': form, 
                    'chapter': chapter,
                    'easy_count': easy_count,
                    'medium_count': medium_count,
                    'hard_count': hard_count,
                    'is_book_quiz': False,
                }
                messages.error(request, f'Only {questions_qs.count()} questions available for selected criteria.')
                return render(request, 'quiz/start_quiz.html', context)
            
            # Create quiz
            quiz = Quiz.objects.create(
                user=request.user,
                chapter=chapter,
                title=f"{chapter.title} Quiz",
                total_questions=num_questions,
                duration_minutes=duration_minutes
            )
            
            # Select random questions
            questions = random.sample(list(questions_qs), num_questions)
            
            # Store question IDs in session
            request.session[f'quiz_{quiz.id}_questions'] = [q.id for q in questions]
            request.session[f'quiz_{quiz.id}_current'] = 0
            
            return redirect('quiz:take_quiz', quiz_id=quiz.id)
    else:
        form = QuizSelectionForm()
        form.fields['chapter'].queryset = Chapter.objects.filter(id=chapter_id)
        form.fields['chapter'].initial = chapter
        form.fields['quiz_type'].initial = 'chapter'
        
        # Set intelligent default for number of questions
        total_questions = get_questions_for_source(chapter).count()
        suggested_questions = min(10, total_questions)  # Default to 10 or max available
        form.fields['num_questions'].initial = suggested_questions
        if total_questions > 0:
            form.fields['num_questions'].widget.attrs['max'] = total_questions
    
    # Calculate difficulty counts
    all_questions = get_questions_for_source(chapter)
    easy_count = all_questions.filter(difficulty='easy').count()
    medium_count = all_questions.filter(difficulty='medium').count()
    hard_count = all_questions.filter(difficulty='hard').count()
    
    context = {
        'form': form, 
        'chapter': chapter,
        'easy_count': easy_count,
        'medium_count': medium_count,
        'hard_count': hard_count,
        'is_book_quiz': False,
    }
    return render(request, 'quiz/start_quiz.html', context)


@login_required
def start_book_quiz(request, book_id):
    """Start a new book quiz"""
    book = get_object_or_404(Book, id=book_id)
    
    if request.method == 'POST':
        form = QuizSelectionForm(request.POST)
        form.fields['book'].queryset = Book.objects.filter(id=book_id)
        form.fields['book'].initial = book
        form.fields['quiz_type'].initial = 'book'
        
        if form.is_valid():
            num_questions = form.cleaned_data['num_questions']
            difficulty = form.cleaned_data['difficulty']
            duration_minutes = int(form.cleaned_data['duration_minutes'])
            
            # Get questions based on difficulty from all chapters in the book
            questions_qs = get_questions_for_source(book, difficulty)
            
            if questions_qs.count() < num_questions:
                # Calculate difficulty counts for error response
                all_questions = get_questions_for_source(book)
                easy_count = all_questions.filter(difficulty='easy').count()
                medium_count = all_questions.filter(difficulty='medium').count()
                hard_count = all_questions.filter(difficulty='hard').count()
                
                context = {
                    'form': form, 
                    'book': book,
                    'easy_count': easy_count,
                    'medium_count': medium_count,
                    'hard_count': hard_count,
                    'is_book_quiz': True,
                }
                messages.error(request, f'Only {questions_qs.count()} questions available for selected criteria.')
                return render(request, 'quiz/start_quiz.html', context)
            
            # Create quiz
            quiz = Quiz.objects.create(
                user=request.user,
                book=book,
                title=f"{book.title} - Complete Book Quiz",
                total_questions=num_questions,
                duration_minutes=duration_minutes
            )
            
            # Select random questions
            questions = random.sample(list(questions_qs), num_questions)
            
            # Store question IDs in session
            request.session[f'quiz_{quiz.id}_questions'] = [q.id for q in questions]
            request.session[f'quiz_{quiz.id}_current'] = 0
            
            return redirect('quiz:take_quiz', quiz_id=quiz.id)
    else:
        form = QuizSelectionForm()
        form.fields['book'].queryset = Book.objects.filter(id=book_id)
        form.fields['book'].initial = book
        form.fields['quiz_type'].initial = 'book'
        
        # Set intelligent default for number of questions
        total_questions = get_questions_for_source(book).count()
        suggested_questions = min(10, total_questions)  # Default to 10 or max available
        form.fields['num_questions'].initial = suggested_questions
        if total_questions > 0:
            form.fields['num_questions'].widget.attrs['max'] = total_questions
    
    # Calculate difficulty counts for the entire book
    all_questions = get_questions_for_source(book)
    easy_count = all_questions.filter(difficulty='easy').count()
    medium_count = all_questions.filter(difficulty='medium').count()
    hard_count = all_questions.filter(difficulty='hard').count()
    
    context = {
        'form': form, 
        'book': book,
        'easy_count': easy_count,
        'medium_count': medium_count,
        'hard_count': hard_count,
        'is_book_quiz': True,
    }
    return render(request, 'quiz/start_quiz.html', context)


@login_required
def take_quiz(request, quiz_id):
    """Take a quiz"""
    quiz = get_object_or_404(Quiz, id=quiz_id, user=request.user, is_completed=False)
    
    # Get questions from session
    question_ids = request.session.get(f'quiz_{quiz.id}_questions', [])
    current_index = request.session.get(f'quiz_{quiz.id}_current', 0)
    
    if not question_ids or current_index >= len(question_ids):
        return redirect('quiz:quiz_results', quiz_id=quiz.id)
    
    question = get_object_or_404(Question, id=question_ids[current_index])
    
    # Handle form submissions
    if request.method == 'POST':
        action = request.POST.get('action', 'next')
        user_answer = request.POST.get('answer', '').strip()
        
        if action == 'mark_for_review':
            # Mark question for review
            status, created = QuizQuestionStatus.objects.get_or_create(
                quiz=quiz,
                question=question,
                defaults={'status': 'marked_for_review'}
            )
            if not created:
                if status.status == 'attempted':
                    status.status = 'answered_and_marked'
                else:
                    status.status = 'marked_for_review'
                status.save()
            messages.info(request, 'Question marked for review.')
            
        elif action == 'clear_answer':
            # Clear the answer for this question
            try:
                quiz_answer = QuizAnswer.objects.get(quiz=quiz, question=question)
                quiz_answer.delete()
                messages.success(request, 'Answer cleared successfully.')
            except QuizAnswer.DoesNotExist:
                messages.info(request, 'No answer to clear for this question.')
            
            # Update question status to unattempted
            try:
                status = QuizQuestionStatus.objects.get(quiz=quiz, question=question)
                if status.status in ['attempted', 'answered_and_marked']:
                    if status.status == 'answered_and_marked':
                        status.status = 'marked_for_review'
                    else:
                        status.status = 'unattempted'
                    status.save()
            except QuizQuestionStatus.DoesNotExist:
                # Create unattempted status if it doesn't exist
                QuizQuestionStatus.objects.create(
                    quiz=quiz,
                    question=question,
                    status='unattempted'
                )
            
        elif action == 'next' and user_answer:
            # Check if answer is correct
            is_correct = user_answer.lower() == question.correct_answer.lower()
            
            # Save or update answer
            quiz_answer, created = QuizAnswer.objects.get_or_create(
                quiz=quiz,
                question=question,
                defaults={
                    'user_answer': user_answer,
                    'is_correct': is_correct
                }
            )
            if not created:
                quiz_answer.user_answer = user_answer
                quiz_answer.is_correct = is_correct
                quiz_answer.save()
            
            # Update question status
            status, created = QuizQuestionStatus.objects.get_or_create(
                quiz=quiz,
                question=question,
                defaults={'status': 'attempted'}
            )
            if not created:
                if status.status == 'marked_for_review':
                    status.status = 'answered_and_marked'
                else:
                    status.status = 'attempted'
                status.save()
            
            # Move to next question
            request.session[f'quiz_{quiz.id}_current'] = current_index + 1
            
            if current_index + 1 >= len(question_ids):
                # Quiz completed
                return redirect('quiz:quiz_results', quiz_id=quiz.id)
            else:
                return redirect('quiz:take_quiz', quiz_id=quiz.id)
                
        elif action == 'jump_to':
            # Jump to specific question
            target_index = int(request.POST.get('question_index', 0))
            if 0 <= target_index < len(question_ids):
                request.session[f'quiz_{quiz.id}_current'] = target_index
                return redirect('quiz:take_quiz', quiz_id=quiz.id)
        
        if not user_answer and action == 'next':
            messages.error(request, 'Please provide an answer.')
    
    # Get question statuses for all questions
    question_statuses = {}
    statuses = QuizQuestionStatus.objects.filter(quiz=quiz, question_id__in=question_ids)
    for status in statuses:
        question_statuses[status.question_id] = status.status
    
    # Get answered questions
    answered_question_ids = set(QuizAnswer.objects.filter(
        quiz=quiz, 
        question_id__in=question_ids
    ).values_list('question_id', flat=True))
    
    # Count question statuses
    total_questions = len(question_ids)
    attempted_count = len(answered_question_ids)
    marked_count = len([s for s in question_statuses.values() if 'marked' in s])
    unattempted_count = total_questions - attempted_count
    
    progress = ((current_index + 1) / len(question_ids)) * 100
    
    # Get current answer if exists
    current_answer = None
    try:
        current_answer = QuizAnswer.objects.get(quiz=quiz, question=question)
    except QuizAnswer.DoesNotExist:
        pass
    
    context = {
        'quiz': quiz,
        'question': question,
        'question_number': current_index + 1,
        'total_questions': len(question_ids),
        'progress': progress,
        'question_ids': question_ids,
        'current_index': current_index,
        'question_statuses': question_statuses,
        'attempted_count': attempted_count,
        'marked_count': marked_count,
        'unattempted_count': unattempted_count,
        'current_answer': current_answer,
    }
    return render(request, 'quiz/take_quiz.html', context)


@login_required
def quiz_results(request, quiz_id):
    """Show quiz results"""
    quiz = get_object_or_404(Quiz, id=quiz_id, user=request.user)
    
    if not quiz.is_completed:
        # Calculate results with new scoring system
        answers = quiz.answers.all()
        correct_answers = answers.filter(is_correct=True).count()
        wrong_answers = answers.filter(is_correct=False).count()
        total_attempted = answers.count()
        total_questions = quiz.total_questions
        unattempted_questions = total_questions - total_attempted
        
        # New scoring formula: +1 for correct, -0.25 for wrong, 0 for unattempted
        raw_score = (correct_answers * 1.0) + (wrong_answers * -0.25) + (unattempted_questions * 0)
        
        # Calculate percentage score (out of total possible marks)
        max_possible_score = total_questions * 1.0  # Maximum if all answers were correct
        if max_possible_score > 0:
            percentage_score = max(0, (raw_score / max_possible_score) * 100)  # Ensure non-negative
        else:
            percentage_score = 0
        
        # Update quiz
        quiz.end_time = timezone.now()
        quiz.score = percentage_score
        quiz.correct_answers = correct_answers
        quiz.is_completed = True
        quiz.save()
        
        # Clean up session
        session_keys = [f'quiz_{quiz.id}_questions', f'quiz_{quiz.id}_current']
        for key in session_keys:
            request.session.pop(key, None)
    
    # Recalculate stats for display
    answers = quiz.answers.select_related('question').order_by('answered_at')
    correct_count = answers.filter(is_correct=True).count()
    wrong_count = answers.filter(is_correct=False).count()
    attempted_count = answers.count()
    unattempted_count = quiz.total_questions - attempted_count
    
    # Calculate detailed scoring breakdown
    raw_score = (correct_count * 1.0) + (wrong_count * -0.25) + (unattempted_count * 0)
    max_possible = quiz.total_questions * 1.0
    
    context = {
        'quiz': quiz,
        'answers': answers,
        'correct_count': correct_count,
        'wrong_count': wrong_count,
        'attempted_count': attempted_count,
        'unattempted_count': unattempted_count,
        'raw_score': raw_score,
        'max_possible_score': max_possible,
    }
    return render(request, 'quiz/quiz_results.html', context)


@login_required
def quiz_history(request):
    """Show user's quiz history"""
    quizzes = Quiz.objects.filter(user=request.user, is_completed=True).select_related('chapter', 'chapter__book').order_by('-end_time')
    
    # Pagination
    paginator = Paginator(quizzes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'quiz/quiz_history.html', context)


def books_list(request):
    """List all books with their chapters"""
    books = Book.objects.prefetch_related('chapters__questions').order_by('title')
    
    # Add question counts for each book
    for book in books:
        book.total_questions = sum(chapter.questions.count() for chapter in book.chapters.all())
    
    return render(request, 'quiz/books_list.html', {'books': books})


def chapter_questions(request, chapter_id):
    """View questions in a chapter"""
    chapter = get_object_or_404(Chapter, id=chapter_id)
    questions = chapter.questions.order_by('created_at')
    
    # Calculate difficulty counts
    easy_count = questions.filter(difficulty='easy').count()
    medium_count = questions.filter(difficulty='medium').count()
    hard_count = questions.filter(difficulty='hard').count()
    
    # Pagination
    paginator = Paginator(questions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'chapter': chapter,
        'page_obj': page_obj,
        'easy_count': easy_count,
        'medium_count': medium_count,
        'hard_count': hard_count,
    }
    return render(request, 'quiz/chapter_questions.html', context)


# Authentication views
class CustomLoginView(auth_views.LoginView):
    template_name = 'quiz/login.html'
    redirect_authenticated_user = True
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['username'].widget.attrs.update({'class': 'form-control'})
        form.fields['password'].widget.attrs.update({'class': 'form-control'})
        return form
    
    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return '/quiz/'


class CustomLogoutView(auth_views.LogoutView):
    next_page = 'quiz:home'
