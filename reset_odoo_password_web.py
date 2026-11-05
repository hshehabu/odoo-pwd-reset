import os
import sys
import psycopg2
from passlib.context import CryptContext
from dotenv import load_dotenv
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import webbrowser
import threading
import json

load_dotenv()

# Load environment variables
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
USER_ID = os.getenv("USER_ID")
NEW_PASSWORD = os.getenv("NEW_PASSWORD")
LOGIN = os.getenv("LOGIN")

required_vars = {
    "DB_HOST": DB_HOST,
    "DB_PORT": DB_PORT,
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
    "USER_ID": USER_ID,
    "LOGIN": LOGIN,
    "NEW_PASSWORD": NEW_PASSWORD,
}

missing = [key for key, value in required_vars.items() if value is None]
if missing:
    print(f"Error: Missing required environment variables: {', '.join(missing)}")
    print("Please check your .env file.")
    input("Press Enter to exit...")
    sys.exit(1)

USER_ID = int(USER_ID)

pwd_context = CryptContext(
    schemes=["pbkdf2_sha512"],
    default="pbkdf2_sha512",
    pbkdf2_sha512__default_rounds=60000,
)

hashed_password = pwd_context.hash(NEW_PASSWORD)

HTML_PAGE = """<!DOCTYPE html>
<html>
<head>
    <title>Odoo Password Reset</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 500px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-top: 0;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #555;
        }
        input {
            width: 100%;
            padding: 10px;
            font-size: 14px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        button {
            background: #007bff;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
            width: 100%;
            margin-top: 15px;
        }
        button:hover {
            background: #0056b3;
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        #status {
            margin-top: 15px;
            padding: 10px;
            border-radius: 4px;
            display: none;
        }
        .success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Odoo Password Reset</h1>
        <form id="resetForm">
            <label for="dbname">Database Name:</label>
            <input type="text" id="dbname" name="dbname" required autofocus>
            <button type="submit" id="submitBtn">Reset Password</button>
        </form>
        <div id="status"></div>
    </div>
    <script>
        document.getElementById('resetForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const dbname = document.getElementById('dbname').value.trim();
            const submitBtn = document.getElementById('submitBtn');
            const status = document.getElementById('status');
            
            if (!dbname) {
                status.textContent = 'Please enter a database name!';
                status.className = 'error';
                status.style.display = 'block';
                return;
            }
            
            submitBtn.disabled = true;
            submitBtn.textContent = 'Resetting...';
            status.textContent = 'Resetting password...';
            status.className = 'info';
            status.style.display = 'block';
            
            try {
                const response = await fetch('/reset', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: 'dbname=' + encodeURIComponent(dbname)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    status.textContent = 'Password reset successful!';
                    status.className = 'success';
                    document.getElementById('dbname').value = '';
                } else {
                    status.textContent = 'Error: ' + result.error;
                    status.className = 'error';
                }
            } catch (error) {
                status.textContent = 'Error: ' + error.message;
                status.className = 'error';
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Reset Password';
            }
        });
    </script>
</body>
</html>"""


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/reset':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = urllib.parse.parse_qs(post_data)
            db_name = params.get('dbname', [''])[0].strip()
            
            if not db_name:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': 'Database name is required'}).encode())
                return
            
            try:
                conn = psycopg2.connect(
                    dbname=db_name,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    host=DB_HOST,
                    port=DB_PORT,
                )
                cur = conn.cursor()
                cur.execute(
                    "UPDATE res_users SET login = %s, password = %s WHERE id = %s",
                    (LOGIN, hashed_password, USER_ID)
                )
                
                conn.commit()
                cur.close()
                conn.close()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'message': f'Password reset successful for database: {db_name}'}).encode())
                
            except Exception as e:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress server logs


def open_browser():
    import time
    time.sleep(1)  # Wait for server to start
    webbrowser.open('http://localhost:1111')


if __name__ == '__main__':
    server = HTTPServer(('localhost', 1111), RequestHandler)
    
    # Open browser in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    print("Server started at http://localhost:1111")
    print("Browser should open automatically. Press Ctrl+C to stop the server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.shutdown()


