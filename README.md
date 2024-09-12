# Flask App Deployment

This is a simple Flask app configured for deployment on a DigitalOcean droplet using Nginx.

## Files

- `app.py`: The main Flask application
- `requirements.txt`: Python dependencies
- `flask_app.service`: Systemd service file for running the app

## Local Setup

1. Clone this repository
2. Create a virtual environment: `python3 -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run the app locally: `flask run --host=127.0.0.1 --port=8000`

## Droplet Deployment Steps

1. Create a new DigitalOcean droplet and SSH into it.

2. Update the system:
   ```
   sudo apt update && sudo apt upgrade -y
   ```

3. Install Python and pip:
   ```
   sudo apt install python3 python3-pip python3-venv -y
   ```

4. Create a directory for your app:
   ```
   mkdir ~/flask-app && cd ~/flask-app
   ```

5. Clone this repository:
   ```
   git clone https://github.com/yourusername/your-repo-name.git .
   ```

6. Create and activate a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

7. Install the requirements:
   ```
   pip install -r requirements.txt
   ```

8. Copy the `flask_app.service` file to the system directory:
   ```
   sudo cp flask_app.service /etc/systemd/system/
   ```

9. Edit the `flask_app.service` file to replace `your_username` with your actual username:
   ```
   sudo nano /etc/systemd/system/flask_app.service
   ```

10. Start and enable the Flask app service:
    ```
    sudo systemctl start flask_app
    sudo systemctl enable flask_app
    ```

11. Install Nginx:
    ```
    sudo apt install nginx -y
    ```

12. Create a new Nginx config file:
    ```
    sudo nano /etc/nginx/sites-available/flask_app
    ```
    Add the following content (replace `your_domain.com` with your actual domain or droplet IP):
    ```
    server {
        listen 80;
        server_name your_domain.com;

        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
    ```

13. Enable the Nginx site:
    ```
    sudo ln -s /etc/nginx/sites-available/flask_app /etc/nginx/sites-enabled
    sudo nginx -t
    sudo systemctl restart nginx
    ```

14. Configure the firewall:
    ```
    sudo ufw allow 'Nginx Full'
    sudo ufw enable
    ```

Your Flask app should now be running on your DigitalOcean droplet and accessible via your domain name or the droplet's IP address.

Note: This setup uses Flask's built-in development server, which is not recommended for production use. For a production environment, consider using a WSGI server like Gunicorn or uWSGI for better performance and reliability.