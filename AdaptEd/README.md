# AdaptEd - AI-Powered Adaptive Learning Platform

AdaptEd is an AI-powered adaptive learning platform designed for school students in grades 5-9. The platform aims to provide personalized learning experiences by adapting to the individual needs of each student.

## Project Structure

```
AdaptEd
├── backend
│   ├── app.py               # Entry point for the FastAPI backend
│   ├── models
│   │   └── user.py          # User model definition
│   ├── routes
│   │   ├── lessons.py       # Routes for generating math tasks
│   │   └── users.py         # Routes for user interactions
│   ├── services
│   │   └── recommendation.py # Logic for generating recommendations
│   ├── utils
│   │   └── database.py      # In-memory storage for tasks and user data
│   └── requirements.txt     # Backend dependencies
├── frontend
│   ├── app.py               # Entry point for the Streamlit frontend
│   ├── components
│   │   ├── dashboard.py      # Dashboard view components
│   │   └── quiz.py           # Quiz interface components
│   └── requirements.txt      # Frontend dependencies
├── README.md                # Project documentation
└── .gitignore               # Files to be ignored by version control
```

## Features

- **User Management**: Allows users to register, log in, and track their progress.
- **Adaptive Learning**: Generates personalized math tasks based on user performance.
- **Feedback Mechanism**: Provides instant feedback on user answers and recommendations for improvement.
- **Dashboard**: Displays user statistics and progress over time.

## Setup Instructions

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd AdaptEd
   ```

2. **Set up the backend**:
   - Navigate to the `backend` directory:
     ```
     cd backend
     ```
   - Install the required dependencies:
     ```
     pip install -r requirements.txt
     ```
   - Run the FastAPI application:
     ```
     uvicorn app:app --reload
     ```

3. **Set up the frontend**:
   - Navigate to the `frontend` directory:
     ```
     cd ../frontend
     ```
   - Install the required dependencies:
     ```
     pip install -r requirements.txt
     ```
   - Run the Streamlit application:
     ```
     streamlit run app.py
     ```

## Usage

- Access the frontend application in your web browser at `http://localhost:8501`.
- Interact with the platform by completing math tasks and viewing your progress on the dashboard.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.