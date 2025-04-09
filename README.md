# AI Agent Platform

A powerful platform for managing AI agents and their tasks. This application allows users to create, manage, and monitor AI agents while tracking their performance and analytics.

## Features

- **Agent Management**: Create and manage different types of AI agents
- **Task Assignment**: Assign tasks to specific agents
- **Performance Tracking**: Monitor agent performance and success rates
- **Analytics Dashboard**: View detailed analytics and task distribution
- **User Authentication**: Secure user registration and login
- **Dark Mode UI**: Modern, clean interface with dark theme

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-agent-platform.git
cd ai-agent-platform
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file with the following variables:
```
FLASK_APP=main.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key
```

5. Initialize the database:
```bash
python init_db.py
```

6. Run the application:
```bash
python main.py
```

## Project Structure

```
ai-agent-platform/
├── agents/                 # AI agent implementations
├── static/                 # Static files (CSS, JS, images)
├── templates/              # HTML templates
├── models.py              # Database models
├── main.py                # Main application file
├── init_db.py             # Database initialization
├── requirements.txt       # Project dependencies
└── README.md              # Project documentation
```

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
