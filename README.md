# Quiz App

A comprehensive Django-based quiz application that allows you to create books, add chapters, upload questions via JSON, and take interactive quizzes with detailed history tracking.

## Features

### Core Functionality
- **Book Management**: Add books with title, author, and description
- **Chapter Management**: Add chapters to books with chapter numbers
- **Question Upload**: Upload questions in JSON format with multiple question types
- **Interactive Quizzes**: Take quizzes with configurable difficulty and question count
- **Quiz History**: Track all quiz attempts with detailed results and statistics

### Question Types Supported
- Multiple Choice Questions
- True/False Questions
- Short Answer Questions

### Additional Features
- User authentication and personal quiz history
- Admin interface for content management
- Responsive Bootstrap-based UI
- Question difficulty levels (Easy, Medium, Hard)
- Detailed explanations for answers
- Progress tracking during quizzes
- Performance statistics and analytics

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Quick Start

1. **Navigate to the project directory**:
   ```bash
   cd "quiz_app"
   ```

2. **Activate the virtual environment**:
   ```bash
   .venv\Scripts\activate
   ```

3. **Start the development server**:
   ```bash
   python manage.py runserver
   ```

4. **Access the application**:
   Open your browser and go to `http://127.0.0.1:8000/`

### Admin Access
- **Admin URL**: `http://127.0.0.1:8000/admin/`
- **Username**: `admin`
- **Password**: `admin`

## Usage Guide

### 1. Adding Books and Chapters

1. **Add a Book**:
   - Navigate to "Manage" > "Add Book"
   - Fill in the book title, author, and optional description
   - Click "Add Book"

2. **Add Chapters**:
   - Navigate to "Manage" > "Add Chapter"
   - Select the book from the dropdown
   - Enter chapter title, number, and optional description
   - Click "Add Chapter"

### 2. Uploading Questions

1. **Navigate to "Manage" > "Upload Questions"**
2. **Select the target chapter**
3. **Prepare your questions in JSON format** (see sample below)
4. **Paste the JSON and click "Upload Questions"**

#### Sample Question JSON Format:

The system supports two JSON formats:

**Format 1 (Simplified):**
```json
[
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
]
```

**Format 2 (Extended):**
```json
[
    {
        "question_text": "What is the capital of France?",
        "question_type": "multiple_choice",
        "options": {"A": "London", "B": "Berlin", "C": "Paris", "D": "Madrid"},
        "correct_answer": "C",
        "explanation": "Paris is the capital and largest city of France.",
        "difficulty": "easy"
    }
]
```

#### JSON Field Reference:

**Format 1 Fields:**
- `question`: The question content (required)
- `options`: Object with answer choices (required for multiple choice)
- `answer`: The correct answer (required)
- `difficulty`: Number 1-5 where 1-2=easy, 3=medium, 4-5=hard (optional, defaults to 3)

**Format 2 Fields:**
- `question_text`: The question content (required)
- `question_type`: `"multiple_choice"`, `"true_false"`, or `"short_answer"` (auto-detected if not provided)
- `correct_answer`: The correct answer (required)
- `options`: Object with answer choices (required for multiple_choice)
- `explanation`: Detailed explanation of the answer (optional)
- `difficulty`: `"easy"`, `"medium"`, or `"hard"` (optional, defaults to "medium")

### 3. Taking Quizzes

1. **Login** to your account (required for quiz tracking)
2. **Navigate to "Take Quiz"**
3. **Select a chapter** with available questions
4. **Configure quiz settings**:
   - Number of questions (1-50)
   - Difficulty level filter
5. **Take the quiz** by answering each question
6. **View results** with detailed explanations

### 4. Viewing Quiz History

1. **Navigate to "Quiz History"** (available after login)
2. **View all past quiz attempts** with:
   - Scores and percentages
   - Date and duration
   - Detailed question-by-question breakdown
3. **Retake quizzes** to improve scores

## File Structure

```
quiz_project/
├── manage.py
├── quiz_project/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── quiz/
│   ├── models.py          # Database models
│   ├── views.py           # Application logic
│   ├── forms.py           # Form definitions
│   ├── admin.py           # Admin interface
│   ├── urls.py            # URL routing
│   └── templates/quiz/    # HTML templates
└── sample_questions.json  # Example questions
```

## Database Models

- **Book**: Stores book information (title, author, description)
- **Chapter**: Stores chapter information linked to books
- **Question**: Stores questions with types, options, and answers
- **Quiz**: Tracks individual quiz sessions
- **QuizAnswer**: Records individual question responses

## Technology Stack

- **Backend**: Django 5.2.7
- **Database**: SQLite (default, easily configurable)
- **Frontend**: Bootstrap 5.1.3, Font Awesome 6.0
- **Authentication**: Django's built-in user system

## API Endpoints

The application uses Django's URL routing system:

- `/` - Home page
- `/add-book/` - Add new book
- `/add-chapter/` - Add new chapter
- `/upload-questions/` - Upload questions via JSON
- `/quiz/` - Available quizzes list
- `/quiz/start/<chapter_id>/` - Start quiz for specific chapter
- `/quiz/take/<quiz_id>/` - Take active quiz
- `/quiz/results/<quiz_id>/` - View quiz results
- `/quiz/history/` - View quiz history
- `/books/` - List all books and chapters
- `/admin/` - Django admin interface

## Customization

### Adding New Question Types
1. Update the `QUESTION_TYPES` choices in `models.py`
2. Modify the form validation in `forms.py`
3. Update the quiz-taking template to handle the new type

### Styling Changes
- Edit the CSS in `templates/quiz/base.html`
- Modify Bootstrap classes in individual templates
- Add custom static files if needed

## Troubleshooting

### Common Issues

1. **Server won't start**: Make sure you're in the correct directory and virtual environment is activated
2. **Admin login fails**: Use username `admin` and password `admin`
3. **Questions not uploading**: Check JSON format against the provided example
4. **Database errors**: Run `python manage.py migrate` to apply migrations

### Getting Help

For technical issues:
1. Check the terminal output for error messages
2. Verify the JSON format for question uploads
3. Ensure all required fields are filled in forms
4. Check that books and chapters exist before uploading questions

## License

This project is created for educational purposes. Feel free to modify and extend it for your needs.