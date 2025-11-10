from django.db import models
from django.contrib.auth.models import User
import json


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['title']


class Chapter(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=200)
    chapter_number = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.book.title} - Chapter {self.chapter_number}: {self.title}"
    
    class Meta:
        ordering = ['book', 'chapter_number']
        unique_together = ['book', 'chapter_number']


class Question(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    options = models.JSONField(default=dict, help_text="Multiple choice options: {'A': 'option1', 'B': 'option2', etc.}")
    correct_answer = models.CharField(max_length=500)
    explanation = models.TextField(blank=True)
    difficulty = models.CharField(max_length=10, choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')], default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.chapter} - {self.question_text[:50]}..."
    
    class Meta:
        ordering = ['chapter', 'created_at']


class Quiz(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=30, help_text="Quiz duration in minutes")
    score = models.FloatField(null=True, blank=True)
    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    
    def get_score_breakdown(self):
        """Calculate detailed score breakdown with new scoring system"""
        answers = self.answers.all()
        correct_count = answers.filter(is_correct=True).count()
        wrong_count = answers.filter(is_correct=False).count()
        attempted_count = answers.count()
        unattempted_count = self.total_questions - attempted_count
        
        # Scoring: +1 for correct, -0.25 for wrong, 0 for unattempted
        raw_score = (correct_count * 1.0) + (wrong_count * -0.25) + (unattempted_count * 0)
        max_possible = self.total_questions * 1.0
        
        return {
            'correct_count': correct_count,
            'wrong_count': wrong_count,
            'attempted_count': attempted_count,
            'unattempted_count': unattempted_count,
            'raw_score': raw_score,
            'max_possible': max_possible,
            'percentage': max(0, (raw_score / max_possible) * 100) if max_possible > 0 else 0
        }
    
    def get_quiz_source(self):
        """Return the source of the quiz (book or chapter)"""
        if self.book:
            return self.book
        elif self.chapter:
            return self.chapter
        return None
    
    def get_quiz_type(self):
        """Return whether this is a book or chapter quiz"""
        if self.book:
            return 'book'
        elif self.chapter:
            return 'chapter'
        return 'unknown'
    
    def __str__(self):
        source = "Book Quiz" if self.book else "Chapter Quiz"
        if self.score is not None:
            return f"{self.user.username} - {source}: {self.title} ({self.score}%)"
        return f"{self.user.username} - {source}: {self.title}"
    
    class Meta:
        ordering = ['-start_time']
        constraints = [
            models.CheckConstraint(
                check=models.Q(chapter__isnull=False, book__isnull=True) | 
                      models.Q(chapter__isnull=True, book__isnull=False),
                name='quiz_either_chapter_or_book'
            )
        ]


class QuizAnswer(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user_answer = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.quiz} - Q: {self.question.question_text[:30]}..."
    
    class Meta:
        ordering = ['answered_at']


class QuizQuestionStatus(models.Model):
    STATUS_CHOICES = [
        ('unattempted', 'Unattempted'),
        ('attempted', 'Attempted'),
        ('marked_for_review', 'Marked for Review'),
        ('answered_and_marked', 'Answered and Marked for Review'),
    ]
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='question_statuses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unattempted')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['quiz', 'question']
        ordering = ['quiz', 'question']
    
    def __str__(self):
        return f"{self.quiz} - Q{self.question.id}: {self.status}"
