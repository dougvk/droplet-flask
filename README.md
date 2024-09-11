# Flask App Deployment

This is a simple Flask app configured for deployment on a DigitalOcean droplet using Gunicorn and Nginx.

## Files

- `app.py`: The main Flask application
- `requirements.txt`: Python dependencies
- `gunicorn_config.py`: Gunicorn configuration
- `flask_app.service`: Systemd service file for running the app

## Setup

1. Clone this repository
2. Create a virtual environment: `python3 -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run the app locally: `python app.py`

For deployment instructions, please refer to the comments in the code files.