# Social Media Management System

A Flask-based web application for managing multiple social media accounts and automating content posting.

## Features

- User Authentication (Register/Login)
- Social Media Integration:
  - Facebook
  - Instagram
  - Twitter
- Video Creation and Management
- Automated Post Scheduling
- Dashboard for Analytics

## Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd social-media-manager
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

4. Create a `.env` file in the root directory and add your credentials:
```env
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///social_media.db

# Social Media API Keys
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_APP_SECRET=your_facebook_app_secret

INSTAGRAM_APP_ID=your_instagram_app_id
INSTAGRAM_APP_SECRET=your_instagram_app_secret

TWITTER_CLIENT_ID=your_twitter_client_id
TWITTER_CLIENT_SECRET=your_twitter_client_secret

# JSON2Video API
JSON2VIDEO_API_KEY=your_json2video_api_key
```

5. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

## Usage

1. Start the development server:
```bash
python main.py
```

2. Open your browser and navigate to `http://localhost:5000`

3. Register a new account and connect your social media accounts

## Project Structure

```
social-media-manager/
├── main.py              # Main application file
├── requirements.txt     # Project dependencies
├── .env                # Environment variables (not in repo)
├── .gitignore         # Git ignore file
├── README.md          # Project documentation
├── static/            # Static files (CSS, JS, images)
└── templates/         # HTML templates
    ├── base.html
    ├── index.html
    ├── login.html
    ├── register.html
    ├── dashboard.html
    └── ...
```

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/improvement`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add new feature'`)
5. Push to the branch (`git push origin feature/improvement`)
6. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 