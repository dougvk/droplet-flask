# Deploying Flask App to DigitalOcean

This guide will walk you through deploying the Flask app to a DigitalOcean droplet using Nginx as a reverse proxy.

## Prerequisites

- A DigitalOcean account
- A domain name (optional, but recommended)

## Deployment Steps

1. Create a new DigitalOcean droplet (Ubuntu 20.04 LTS recommended)

2. SSH into your droplet:
   ```
   ssh root@your_droplet_ip
   ```

3. Update the system:
   ```
   apt update && apt upgrade -y
   ```

4. Install required packages:
   ```
   apt install python3 python3-pip python3-venv nginx -y
   ```

5. Create a directory for your app:
   ```
   mkdir /root/flask-app && cd /root/flask-app
   ```

6. Clone your repository (replace with your actual repository URL):
   ```
   git clone https://github.com/yourusername/your-repo-name.git .
   ```

7. Create and activate a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

8. Install the requirements:
   ```
   pip install -r requirements.txt
   ```

9. Copy the `flask_app.service` file to the system directory:
   ```
   cp flask_app.service /etc/systemd/system/
   ```

10. Edit the `flask_app.service` file:
    ```
    nano /etc/systemd/system/flask_app.service
    ```
    Update the `WorkingDirectory` and `Environment` paths:
    ```
    WorkingDirectory=/root/flask-app
    Environment="PATH=/root/flask-app/venv/bin"
    ```

11. Start and enable the Flask app service:
    ```
    systemctl start flask_app
    systemctl enable flask_app
    ```

12. Create a new Nginx config file:
    ```
    nano /etc/nginx/sites-available/flask_app
    ```
    Add the following content (replace `your_domain.com` with your domain or droplet IP):
    ```
    server {
        listen 80;
        server_name your_domain.com;

        location / {
            proxy_pass http://127.0.0.1:5000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
    ```

13. Enable the Nginx site:
    ```
    ln -s /etc/nginx/sites-available/flask_app /etc/nginx/sites-enabled
    nginx -t
    systemctl restart nginx
    ```

14. Configure the firewall:
    ```
    ufw allow 'Nginx Full'
    ufw enable
    ```

Your Flask app should now be accessible at `http://your_domain.com` or `http://your_droplet_ip`.

## Updating the App

To update your app after making changes:

1. SSH into your droplet
2. Navigate to your app directory: `cd /root/flask-app`
3. Pull the latest changes: `git pull`
4. Restart the Flask app service: `systemctl restart flask_app`

## Notes

- This setup uses Flask's built-in development server, which is not recommended for high-traffic production environments.
- For better security, consider creating a non-root user to run your app.
- Set up SSL/TLS for HTTPS using Let's Encrypt for a production environment.
