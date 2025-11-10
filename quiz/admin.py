from django.contrib import admin
from .models import Book, Chapter, Question, Quiz, QuizAnswer


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    list_filter = ('created_at', 'author')
    search_fields = ('title', 'author')
    ordering = ('title',)


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('title', 'book', 'chapter_number', 'created_at')
    list_filter = ('book', 'created_at')
    search_fields = ('title', 'book__title')
    ordering = ('book', 'chapter_number')
    list_select_related = ('book',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('get_short_text', 'chapter', 'difficulty', 'created_at')
    list_filter = ('difficulty', 'chapter__book', 'created_at')
    search_fields = ('question_text', 'chapter__title', 'chapter__book__title')
    ordering = ('chapter', 'created_at')
    list_select_related = ('chapter', 'chapter__book')
    
    def get_short_text(self, obj):
        return obj.question_text[:50] + "..." if len(obj.question_text) > 50 else obj.question_text
    get_short_text.short_description = 'Question Text'


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'chapter', 'score', 'total_questions', 'is_completed', 'start_time')
    list_filter = ('is_completed', 'chapter__book', 'start_time')
    search_fields = ('title', 'user__username', 'chapter__title')
    ordering = ('-start_time',)
    list_select_related = ('user', 'chapter', 'chapter__book')
    readonly_fields = ('start_time', 'end_time', 'score', 'total_questions', 'correct_answers')


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'get_short_question', 'user_answer', 'is_correct', 'answered_at')
    list_filter = ('is_correct', 'answered_at', 'quiz__chapter__book')
    search_fields = ('quiz__title', 'question__question_text', 'user_answer')
    ordering = ('-answered_at',)
    list_select_related = ('quiz', 'question', 'quiz__user')
    
    def get_short_question(self, obj):
        return obj.question.question_text[:30] + "..." if len(obj.question.question_text) > 30 else obj.question.question_text
    get_short_question.short_description = 'Question'
