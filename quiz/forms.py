from django import forms
from .models import Book, Chapter, Question
import json


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


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter book title'}),
            'author': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter author name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter book description (optional)'}),
        }


class ChapterForm(forms.ModelForm):
    class Meta:
        model = Chapter
        fields = ['book', 'title', 'chapter_number', 'description']
        widgets = {
            'book': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter chapter title'}),
            'chapter_number': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter chapter number'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter chapter description (optional)'}),
        }


class QuestionUploadForm(forms.Form):
    chapter = forms.ModelChoiceField(
        queryset=Chapter.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the chapter for these questions"
    )
    questions_json = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 15,
            'placeholder': '''[
  {
    "question": "What is the capital of France?",
    "options": {
      "A": "London",
      "B": "Berlin", 
      "C": "Paris",
      "D": "Madrid"
    },
    "answer": "C",
    "difficulty": 2
  }
]'''
        }),
        help_text="Paste your questions in JSON format (supports both formats)"
    )
    
    def clean_questions_json(self):
        questions_json = self.cleaned_data['questions_json']
        try:
            questions = json.loads(questions_json)
            if not isinstance(questions, list):
                raise forms.ValidationError("JSON must be a list of questions")
            
            # Support both formats
            for i, question in enumerate(questions):
                if not isinstance(question, dict):
                    raise forms.ValidationError(f"Question {i+1} must be an object")
                
                # Check for new format (your format)
                if 'question' in question and 'answer' in question:
                    # Convert to internal format
                    if 'question_text' not in question:
                        question['question_text'] = question['question']
                    if 'correct_answer' not in question:
                        question['correct_answer'] = question['answer']
                    
                    # Convert numeric difficulty to string
                    if 'difficulty' in question and isinstance(question['difficulty'], int):
                        difficulty_map = {1: 'easy', 2: 'easy', 3: 'medium', 4: 'hard', 5: 'hard'}
                        question['difficulty'] = difficulty_map.get(question['difficulty'], 'medium')
                
                # Validate required fields (after conversion)
                required_fields = ['question_text', 'correct_answer', 'options']
                for field in required_fields:
                    if field not in question:
                        raise forms.ValidationError(f"Question {i+1} is missing required field: {field}")
                
                # Validate that options is a dictionary
                if not isinstance(question.get('options'), dict):
                    raise forms.ValidationError(f"Question {i+1}: options must be a dictionary")
                
                # Validate difficulty if provided
                if 'difficulty' in question and isinstance(question['difficulty'], int):
                    difficulty_map = {1: 'easy', 2: 'easy', 3: 'medium', 4: 'hard', 5: 'hard'}
                    question['difficulty'] = difficulty_map.get(question['difficulty'], 'medium')
                elif 'difficulty' in question:
                    raise forms.ValidationError(f"Question {i+1} has invalid difficulty. Must be one of: {valid_difficulties}")

            return questions
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f"Invalid JSON format: {str(e)}")


class QuizSelectionForm(forms.Form):
    QUIZ_TYPE_CHOICES = [
        ('chapter', 'Chapter Quiz'),
        ('book', 'Book Quiz'),
    ]
    
    quiz_type = forms.ChoiceField(
        choices=QUIZ_TYPE_CHOICES,
        initial='chapter',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        help_text="Choose whether to take a quiz on a specific chapter or an entire book"
    )
    chapter = forms.ModelChoiceField(
        queryset=Chapter.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select a chapter to take quiz from",
        required=False
    )
    book = forms.ModelChoiceField(
        queryset=Book.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select a book to take quiz from (questions from all chapters)",
        required=False
    )
    num_questions = forms.IntegerField(
        min_value=1,
        max_value=50,
        initial=10,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Number of questions'}),
        help_text="How many questions would you like in this quiz?"
    )
    difficulty = forms.ChoiceField(
        choices=[('all', 'All Difficulties'), ('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')],
        initial='all',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select difficulty level"
    )
    duration_minutes = forms.ChoiceField(
        choices=[
            (15, '15 minutes'),
            (30, '30 minutes'),
            (45, '45 minutes'),
            (60, '1 hour'),
            (90, '1.5 hours'),
            (120, '2 hours'),
        ],
        initial=30,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select quiz duration"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        quiz_type = cleaned_data.get('quiz_type')
        chapter = cleaned_data.get('chapter')
        book = cleaned_data.get('book')
        num_questions = cleaned_data.get('num_questions')
        difficulty = cleaned_data.get('difficulty', 'all')
        
        if quiz_type == 'chapter' and not chapter:
            raise forms.ValidationError("Please select a chapter for chapter quiz.")
        elif quiz_type == 'book' and not book:
            raise forms.ValidationError("Please select a book for book quiz.")
        
        # Validate number of questions against available questions
        if num_questions:
            available_questions = 0
            source = None
            
            if quiz_type == 'chapter' and chapter:
                source = chapter
                available_questions = get_questions_for_source(chapter, difficulty).count()
            elif quiz_type == 'book' and book:
                source = book
                available_questions = get_questions_for_source(book, difficulty).count()
            
            if available_questions > 0 and num_questions > available_questions:
                if quiz_type == 'chapter':
                    if difficulty == 'all':
                        error_msg = f"Only {available_questions} questions available in this chapter."
                    else:
                        error_msg = f"Only {available_questions} {difficulty} questions available in this chapter."
                else:  # book quiz
                    if difficulty == 'all':
                        error_msg = f"Only {available_questions} questions available in this book."
                    else:
                        error_msg = f"Only {available_questions} {difficulty} questions available in this book."
                
                raise forms.ValidationError(error_msg + f" Please select {available_questions} or fewer questions.")
        
        return cleaned_data