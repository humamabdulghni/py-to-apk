from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from flask import Flask, send_file, render_template_string
import threading
import os
import qrcode
import socket
import zipfile

# Flask app for serving files
flask_app = Flask(__name__)
shared_files = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Shared Files</title>
    <style>
        *{
            padding: 0%;
            margin: 0%;
            box-sizing: border-box;
        }
        body {
            font-family: Arial, sans-serif;
            background-color: #333;
            color: #ddd;
            padding: 20px;
              display: flex;
        align-items: center;
     justify-content: center;
     min-height:90%;
    flex-direction: column;
        }
        a,p {
            color: whitew;
            text-decoration: none;
            padding:10px;
            background:#121212;
            width:90vw;
            text-align: center;
            color: white;
        }
        a:hover {
            text-decoration: underline;
        }
        p,p a{
            background-color: #00061f;
        }
        p,a{
            padding: 20px;
            margin: 5px;
        }
    </style>
</head>
<body>
    <h1>Shared Files</h1>

    {% for file in files %}
       <a href="/file/{{ loop.index0 }}">{{ file }}</a>
    {% endfor %}

    <p><a href="/download_all">Download All as ZIP</a></p>
</body>
</html>
"""

@flask_app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, files=[os.path.basename(f) for f in shared_files])

@flask_app.route('/file/<int:file_index>')
def serve_file(file_index):
    file_path = shared_files[file_index]
    return send_file(file_path, as_attachment=True)

@flask_app.route('/download_all')
def download_all():
    if not shared_files:
        return "No files shared", 404
    zip_path = 'shared_files.zip'
    try:
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file_path in shared_files:
                zipf.write(file_path, os.path.basename(file_path))
        return send_file(zip_path, as_attachment=True)
    except Exception as e:
        return str(e), 500

class FileSharingApp(App):
    def build(self):
        Window.clearcolor = (0.01, 0, 0.1, 1)
        
        self.root = BoxLayout(orientation='vertical', padding=2, spacing=2)
        
        self.file_chooser = FileChooserIconView(path='/', width=100,size_hint=(1,10),filters=['*.*'], multiselect=True)
        
        self.share_button = Button(text='Share Files', on_release=self.share_files)
        self.clear_button = Button(text='Clear Shared Files', on_release=self.clear_files)
        self.qr_button = Button(text='Show QR Code', on_release=self.show_qr)
        
        self.root.add_widget(self.file_chooser)
        self.root.add_widget(self.share_button)
        self.root.add_widget(self.clear_button)
        self.root.add_widget(self.qr_button)
        
        return self.root
    
    def share_files(self, instance):
        selected = self.file_chooser.selection
        if not selected:
            popup = Popup(title='Error', content=Label(text='No files selected'), size_hint=(0.5, 0.5))
            popup.open()
            return
        shared_files.extend(selected)
        local_ip = self.get_local_ip()
        file_url = f'http://{local_ip}:5000'
        Clipboard.copy(file_url)
        popup = Popup(title='Success', content=Label(text=f'server on {file_url} (URL copied to clipboard)'), size_hint=(0.5, 0.5))
        popup.open()
    
    def clear_files(self, instance):
        global shared_files
        shared_files = []
        if os.path.exists('shared_files.zip'):
            os.remove('shared_files.zip')
        popup = Popup(title='Success', content=Label(text='Shared files cleared'), size_hint=(0.5, 0.5))
        popup.open()
    
    def show_qr(self, instance):
        if not shared_files:
            popup = Popup(title='Error', content=Label(text='No files shared'), size_hint=(0.5, 0.5))
            popup.open()
            return
        local_ip = self.get_local_ip()
        file_url = f'http://{local_ip}:5000'
        qr = qrcode.make(file_url)
        qr_file_path = 'qr.png'
        qr.save(qr_file_path)
        popup = Popup(title='QR Code', content=Image(source=qr_file_path), size_hint=(0.5, 0.5))
        popup.open()
    
    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip

def run_flask():
    flask_app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    FileSharingApp().run()
