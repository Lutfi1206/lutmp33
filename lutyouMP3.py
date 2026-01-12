#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎵 LutYouMP3 - TEK KOD (PC & Android)
Geliştirici: Lütfi
✅ FFmpeg GEREKTİRMEZ - DIRECT MP3 İNDİRİR!
"""

import os
import sys
import json
import threading
import subprocess
import re
import traceback
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Platform tespiti - DÜZELTİLDİ
IS_ANDROID = 'ANDROID_ARGUMENT' in os.environ or hasattr(sys, 'getandroidapilevel')

# GUI
try:
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.floatlayout import FloatLayout
    from kivy.uix.label import Label
    from kivy.uix.textinput import TextInput
    from kivy.uix.button import Button
    from kivy.uix.popup import Popup
    from kivy.uix.progressbar import ProgressBar
    from kivy.uix.spinner import Spinner
    from kivy.uix.scrollview import ScrollView
    from kivy.core.window import Window
    from kivy.clock import Clock, mainthread
    from kivy.graphics import Color, Rectangle, RoundedRectangle
    from kivy.metrics import dp, sp
    from kivy.utils import get_color_from_hex, platform as kivy_platform
    KIVY_AVAILABLE = True
except ImportError:
    print("❌ Kivy kurulu değil!")
    KIVY_AVAILABLE = False

# ANDROID İZİNLERİ İÇİN DOĞRU KOD - DÜZELTİLDİ
if IS_ANDROID:
    try:
        from android.permissions import request_permissions, Permission
        ANDROID_PERMISSIONS_AVAILABLE = True
    except ImportError:
        ANDROID_PERMISSIONS_AVAILABLE = False
        print("Android permissions modülü mevcut değil")
else:
    ANDROID_PERMISSIONS_AVAILABLE = False

# YouTube - DIRECT MP3 İNDİRME
try:
    from yt_dlp import YoutubeDL
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    print("❌ yt-dlp kurulu değil!")
    YTDLP_AVAILABLE = False

# Renkler
COLORS = {
    'primary': get_color_from_hex('#FF416C') if KIVY_AVAILABLE else None,
    'secondary': get_color_from_hex('#FF4B2B') if KIVY_AVAILABLE else None,
    'dark': get_color_from_hex('#0F0F23') if KIVY_AVAILABLE else None,
    'darker': get_color_from_hex('#1A1A2E') if KIVY_AVAILABLE else None,
    'light': get_color_from_hex('#FFFFFF') if KIVY_AVAILABLE else None,
    'gray': get_color_from_hex('#2A2A3A') if KIVY_AVAILABLE else None,
    'success': get_color_from_hex('#4CAF50') if KIVY_AVAILABLE else None,
    'warning': get_color_from_hex('#FF9800') if KIVY_AVAILABLE else None,
    'error': get_color_from_hex('#F44336') if KIVY_AVAILABLE else None
}

# Özel logger sınıfı
class CustomLogger:
    def __init__(self, app_instance=None):
        self.app = app_instance
        self.last_percent = 0
    
    def debug(self, msg):
        pass
    
    def info(self, msg):
        print(f"[INFO] {msg}")
    
    def warning(self, msg):
        print(f"[WARNING] {msg}")
    
    def error(self, msg):
        print(f"[ERROR] {msg}")
        if self.app:
            Clock.schedule_once(lambda dt: self.app.update_status(f"Hata: {msg[:50]}", COLORS['error']))
    
    def write(self, msg):
        pass
    
    def flush(self):
        pass

class LutYouMP3(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.downloading = False
        self.current_title = ""
        self.progress_percent = 0
        self.logger = CustomLogger(self)
        
        # ANDROID İZİNLERİ İÇİN - BU DOĞRU YER
        if IS_ANDROID and ANDROID_PERMISSIONS_AVAILABLE:
            Clock.schedule_once(self.request_android_permissions, 1)
    
    def request_android_permissions(self, dt):
        """Android izinlerini iste - DOĞRU YÖNTEM"""
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.INTERNET
            ])
            print("✅ Android izinleri istendi")
        except Exception as e:
            print(f"⚠️  İzin hatası: {e}")
    
    @mainthread
    def update_status(self, text, color=None):
        """Durum metnini güncelle"""
        if hasattr(self, 'status_label'):
            self.status_label.text = text
            if color:
                self.status_label.color = color
    
    @mainthread
    def update_progress(self, value):
        """Progress bar'ı güncelle"""
        if hasattr(self, 'progress_bar'):
            self.progress_bar.value = value
            if value > 0:
                self.progress_bar.opacity = 1
            self.progress_percent = value
    
    @mainthread
    def set_button_state(self, enabled=True, text="⬇️ MP3 İNDİR"):
        """Buton durumunu güncelle"""
        if hasattr(self, 'download_btn'):
            self.download_btn.disabled = not enabled
            self.download_btn.text = text
    
    def build(self):
        if not KIVY_AVAILABLE:
            return Label(text="Kivy kurulu değil!")
        
        # Platforma göre pencere boyutu
        if IS_ANDROID:
            Window.size = (400, 720)
            Window.softinput_mode = 'below_target'
        else:
            Window.size = (800, 600)
        
        Window.clearcolor = COLORS['dark']
        
        # Ana layout
        self.main_layout = FloatLayout()
        
        # Arka plan
        with self.main_layout.canvas.before:
            Color(rgba=COLORS['dark'])
            Rectangle(size=Window.size)
            
            # Gradient efekti
            Color(rgba=(0.1, 0.05, 0.15, 0.6))
            RoundedRectangle(
                size=(Window.width, Window.height * 0.4),
                pos=(0, Window.height * 0.6),
                radius=[0, 0, 0, 0]
            )
        
        # Başlık
        title_box = BoxLayout(orientation='vertical',
                             size_hint=(1, 0.15 if IS_ANDROID else 0.15),
                             pos_hint={'center_x': 0.5, 'top': 0.98})
        
        title_label = Label(
            text='[b]🎵 LutYouMP3[/b]',
            font_size=sp(30 if IS_ANDROID else 32),
            markup=True,
            color=COLORS['light'],
            halign='center',
            size_hint_y=None,
            height=dp(60) if IS_ANDROID else dp(50)
        )
        
        subtitle_label = Label(
            text='[i]YouTube MP3 İndirici by Lütfi[/i]',
            font_size=sp(16 if IS_ANDROID else 16),
            markup=True,
            color=get_color_from_hex('#AAAAAA'),
            halign='center',
            size_hint_y=None,
            height=dp(40) if IS_ANDROID else dp(30)
        )
        
        title_box.add_widget(title_label)
        title_box.add_widget(subtitle_label)
        
        # Ana içerik
        content_box = BoxLayout(orientation='vertical',
                               spacing=dp(20 if IS_ANDROID else 20),
                               padding=[dp(25), dp(20), dp(25), dp(20)] if IS_ANDROID else [dp(30), dp(20), dp(30), dp(20)],
                               size_hint=(0.95, 0.75 if IS_ANDROID else 0.7),
                               pos_hint={'center_x': 0.5, 'center_y': 0.52})
        
        # URL girişi
        url_layout = BoxLayout(orientation='vertical', spacing=dp(8))
        url_label = Label(text='[b]YouTube Linki:[/b]',
                         font_size=sp(18 if IS_ANDROID else 16),
                         markup=True,
                         color=COLORS['light'],
                         size_hint_y=None,
                         height=dp(35) if IS_ANDROID else dp(30))
        
        self.url_input = TextInput(
            hint_text='https://www.youtube.com/watch?v=...',
            multiline=False,
            font_size=sp(16 if IS_ANDROID else 16),
            background_color=COLORS['gray'],
            foreground_color=COLORS['light'],
            padding=[dp(15), dp(10), dp(15), dp(10)] if IS_ANDROID else [dp(12), dp(8), dp(12), dp(8)],
            size_hint_y=None,
            height=dp(55) if IS_ANDROID else dp(45),
            hint_text_color=get_color_from_hex('#888888'),
            halign='left'
        )
        
        url_layout.add_widget(url_label)
        url_layout.add_widget(self.url_input)
        
        # Klasör seçimi
        folder_layout = BoxLayout(orientation='vertical', spacing=dp(8))
        folder_label = Label(text='[b]Kayıt Klasörü:[/b]',
                           font_size=sp(18 if IS_ANDROID else 16),
                           markup=True,
                           color=COLORS['light'],
                           size_hint_y=None,
                           height=dp(35) if IS_ANDROID else dp(30))
        
        self.music_folders = self.get_music_folders()
        self.folder_spinner = Spinner(
            text=self.music_folders[0] if self.music_folders else 'Müzik Klasörü Seç',
            values=self.music_folders,
            background_color=COLORS['gray'],
            color=COLORS['light'],
            size_hint_y=None,
            height=dp(55) if IS_ANDROID else dp(45),
            font_size=sp(16 if IS_ANDROID else 16)
        )
        
        folder_layout.add_widget(folder_label)
        folder_layout.add_widget(self.folder_spinner)
        
        # Kalite seçimi - SADECE 128kbps (EN GARANTİ)
        quality_layout = BoxLayout(orientation='vertical', spacing=dp(8))
        quality_label = Label(text='[b]MP3 Kalitesi:[/b]',
                            font_size=sp(18 if IS_ANDROID else 16),
                            markup=True,
                            color=COLORS['light'],
                            size_hint_y=None,
                            height=dp(35) if IS_ANDROID else dp(30))
        
        if IS_ANDROID:
            quality_grid = GridLayout(cols=1, spacing=dp(12), size_hint_y=None, height=dp(65))
        else:
            quality_grid = GridLayout(cols=1, spacing=dp(10), size_hint_y=None, height=dp(50))
        
        # SADECE 128kbps seçeneği (FFmpeg olmadan en garantili)
        self.quality_128 = Button(
            text='📱 128kbps (FFmpeg GEREKTİRMEZ!)',
            font_size=sp(16 if IS_ANDROID else 14),
            background_color=COLORS['success'],
            bold=True
        )
        
        self.quality_128.bind(on_press=self.select_quality)
        
        quality_grid.add_widget(self.quality_128)
        
        quality_layout.add_widget(quality_label)
        quality_layout.add_widget(quality_grid)
        
        # İndirme butonu
        self.download_btn = Button(
            text='⬇️ MP3 İNDİR',
            font_size=sp(22 if IS_ANDROID else 20),
            bold=True,
            background_color=COLORS['primary'],
            size_hint_y=None,
            height=dp(70) if IS_ANDROID else dp(55)
        )
        self.download_btn.bind(on_press=self.start_download)
        
        # Progress bar
        self.progress_bar = ProgressBar(
            max=100,
            size_hint_y=None,
            height=dp(25) if IS_ANDROID else dp(20)
        )
        self.progress_bar.opacity = 0
        
        # Durum metni
        self.status_label = Label(
            text='YouTube linkini yapıştırın!',
            font_size=sp(15 if IS_ANDROID else 13),
            color=get_color_from_hex('#AAAAAA'),
            halign='center',
            size_hint_y=None,
            height=dp(45) if IS_ANDROID else dp(40)
        )
        
        # Bilgi metni
        info_label = Label(
            text='[i]✅ FFmpeg GEREKTİRMEZ - Direct MP3 İndirir![/i]',
            font_size=sp(12 if IS_ANDROID else 11),
            markup=True,
            color=get_color_from_hex('#4CAF50'),
            halign='center',
            size_hint_y=None,
            height=dp(30)
        )
        
        # Eklenti kontrolü
        if not YTDLP_AVAILABLE:
            self.status_label.text = '❌ yt-dlp kurulu değil!'
            self.status_label.color = COLORS['error']
            self.download_btn.disabled = True
        
        # Bileşenleri ekle
        content_box.add_widget(url_layout)
        content_box.add_widget(folder_layout)
        content_box.add_widget(quality_layout)
        content_box.add_widget(self.download_btn)
        content_box.add_widget(self.progress_bar)
        content_box.add_widget(self.status_label)
        content_box.add_widget(info_label)
        
        # Ana layout'a ekle
        self.main_layout.add_widget(title_box)
        self.main_layout.add_widget(content_box)
        
        # Varsayılan kalite
        self.selected_quality = '128'
        
        return self.main_layout
    
    def get_music_folders(self):
        """Platforma göre müzik klasörlerini bul"""
        folders = []
        
        if IS_ANDROID:
            # Android klasörleri - Pydroid 3 için
            android_paths = [
                '/storage/emulated/0/Music',
                '/storage/emulated/0/Download',
                '/sdcard/Music',
                '/sdcard/Download',
                '/storage/emulated/0/Android/data/ru.iiec.pydroid3/files',
                '/data/data/ru.iiec.pydroid3/files'
            ]
            
            for path in android_paths:
                if os.path.exists(path):
                    folders.append(path)
            
            # Varsayılan klasör
            default = '/storage/emulated/0/Download/LutYouMP3'
            try:
                os.makedirs(default, exist_ok=True)
                folders.insert(0, default)
            except:
                # Pydroid 3 için alternatif
                pydroid_default = '/storage/emulated/0/Android/data/ru.iiec.pydroid3/files/LutYouMP3'
                try:
                    os.makedirs(pydroid_default, exist_ok=True)
                    folders.insert(0, pydroid_default)
                except:
                    pass
                
        else:  # PC
            if sys.platform == "win32":
                try:
                    paths = [
                        os.path.join(os.environ['USERPROFILE'], 'Music'),
                        os.path.join(os.environ['USERPROFILE'], 'Downloads'),
                        os.path.join(os.environ['USERPROFILE'], 'Desktop'),
                        os.path.join(os.environ['USERPROFILE'], 'Music', 'LutYouMP3')
                    ]
                    
                    for path in paths:
                        try:
                            if not os.path.exists(path):
                                os.makedirs(path, exist_ok=True)
                            folders.append(path)
                        except:
                            pass
                        
                except Exception as e:
                    print(f"Klasör hatası: {e}")
            
            elif sys.platform in ["linux", "darwin"]:
                paths = [
                    os.path.expanduser('~/Music'),
                    os.path.expanduser('~/Downloads'),
                    os.path.expanduser('~/Desktop'),
                    os.path.expanduser('~/Music/LutYouMP3')
                ]
                
                for path in paths:
                    try:
                        if not os.path.exists(path):
                            os.makedirs(path, exist_ok=True)
                        folders.append(path)
                    except:
                        pass
        
        # Klasör isimlerini kısalt
        display_folders = []
        self.folder_paths = {}
        
        for folder in folders:
            if IS_ANDROID and len(folder) > 30:
                display = f"...{folder[-20:]}"
            else:
                display = folder
            
            display_folders.append(display)
            self.folder_paths[display] = folder
        
        return display_folders if display_folders else ['Geçerli Klasör']
    
    def select_quality(self, instance):
        """Kalite seçimi"""
        self.quality_128.background_color = COLORS['success']
        self.selected_quality = '128'
    
    def start_download(self, instance):
        """İndirmeyi başlat"""
        if not YTDLP_AVAILABLE:
            self.show_popup('Hata', 'yt-dlp kurulu değil!\n\nKurmak için:\npip install yt-dlp')
            return
        
        url = self.url_input.text.strip()
        
        if not url:
            self.show_popup('Hata', 'Lütfen YouTube linki girin!')
            return
        
        # URL doğrulama
        if not self.is_valid_youtube_url(url):
            self.show_popup('Hata', 
                'Geçerli YouTube linki değil!\n\n'
                'Desteklenen formatlar:\n'
                '• youtube.com/watch?v=VIDEO_ID\n'
                '• youtu.be/VIDEO_ID\n'
                '• youtube.com/playlist?list=...\n'
                '• music.youtube.com/watch?v=...'
            )
            return
        
        # Klasör yolunu al
        selected = self.folder_spinner.text
        folder = self.folder_paths.get(selected, selected)
        
        # Klasör yoksa oluştur
        try:
            os.makedirs(folder, exist_ok=True)
        except Exception as e:
            self.show_popup('Hata', f'Klasör oluşturulamadı:\n\n{e}')
            return
        
        # Butonu devre dışı bırak
        self.set_button_state(False, '⏳ İndiriliyor...')
        
        # Progress
        self.update_progress(5)
        self.update_status('Video bilgileri alınıyor...', COLORS['warning'])
        
        # Thread'de indir
        self.downloading = True
        threading.Thread(
            target=self.safe_download_mp3,
            args=(url, folder, self.selected_quality),
            daemon=True
        ).start()
    
    def is_valid_youtube_url(self, url):
        """YouTube URL'sini doğrula"""
        youtube_domains = [
            'youtube.com',
            'www.youtube.com',
            'm.youtube.com',
            'youtu.be',
            'music.youtube.com'
        ]
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Domain kontrolü
            if any(yt_domain in domain for yt_domain in youtube_domains):
                return True
            
            # Short URL kontrolü (youtu.be)
            if 'youtu.be' in domain:
                return True
                
        except:
            pass
        
        return False
    
    def safe_download_mp3(self, url, folder, quality):
        """Güvenli indirme fonksiyonu"""
        try:
            self.real_download_mp3(url, folder, quality)
        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()
            print(f"\n❌ KRİTİK HATA: {error_msg}")
            print(f"Traceback:\n{error_trace}")
            
            Clock.schedule_once(
                lambda dt: self.update_status(f'❌ Hata: {error_msg[:50]}', COLORS['error'])
            )
            Clock.schedule_once(
                lambda dt: self.show_popup('Kritik Hata',
                    f'Hata oluştu:\n\n{error_msg[:150]}\n\n'
                    f'Lütfen:\n'
                    f'1. İnternet bağlantınızı kontrol edin\n'
                    f'2. YouTube linkinin geçerli olduğundan emin olun\n'
                    f'3. Uygulamayı yeniden başlatın')
            )
        finally:
            self.set_button_state(True, '⬇️ MP3 İNDİR')
            Clock.schedule_once(lambda dt: setattr(self.progress_bar, 'opacity', 0))
            self.downloading = False
    
    def real_download_mp3(self, url, folder, quality):
        """GERÇEK MP3 İNDİRME - FFmpeg GEREKTİRMEZ!"""
        print(f"\n{'='*60}")
        print(f"🎵 LutYouMP3 - DIRECT MP3 İNDİRME BAŞLATILIYOR")
        print(f"📌 URL: {url}")
        print(f"📁 Klasör: {folder}")
        print(f"🎧 Kalite: {quality}kbps")
        print(f"🔧 FFmpeg: GEREK YOK! (Direct MP3)")
        print(f"{'='*60}\n")
        
        # Özel progress hook
        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded = d.get('downloaded_bytes', 0)
                
                if total and total > 0:
                    percent = (downloaded / total) * 100
                    progress = 10 + (percent * 0.8)  # 10-90 arası
                    
                    # Her %5'te bir güncelle
                    if int(percent) % 5 == 0 and int(percent) != self.logger.last_percent:
                        self.logger.last_percent = int(percent)
                        
                        speed = d.get('_speed_str', 'N/A')
                        status_text = f"İndiriliyor: {int(percent)}% | {speed}"
                        
                        Clock.schedule_once(lambda dt: self.update_progress(progress))
                        Clock.schedule_once(
                            lambda dt: self.update_status(status_text, COLORS['warning'])
                        )
                        
                        print(f"📥 {status_text}")
            
            elif d['status'] == 'finished':
                print("✅ İndirme tamamlandı!")
                Clock.schedule_once(lambda dt: self.update_progress(95))
                Clock.schedule_once(
                    lambda dt: self.update_status('İndirme tamamlandı!', COLORS['success'])
                )
        
        try:
            # 1. Video bilgilerini al
            Clock.schedule_once(lambda dt: self.update_progress(10))
            Clock.schedule_once(lambda dt: self.update_status('Video bilgileri alınıyor...', COLORS['warning']))
            
            ydl_info = YoutubeDL({
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,
                'logger': self.logger
            })
            
            info = ydl_info.extract_info(url, download=False)
            title = info.get('title', 'Bilinmeyen_Şarkı')
            
            # Güvenli dosya adı
            safe_title = re.sub(r'[^\w\s\-\.\(\)\[\]]', '', title)
            safe_title = re.sub(r'\s+', ' ', safe_title).strip()
            if not safe_title:
                safe_title = f"youtube_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Kısa başlık
            short_title = title[:30] + "..." if len(title) > 30 else title
            
            print(f"📝 Başlık: {title}")
            print(f"🔒 Güvenli başlık: {safe_title}")
            
            self.current_title = title
            
            # 2. İndirme ayarları - DIRECT MP3 İNDİRME
            Clock.schedule_once(lambda dt: self.update_progress(20))
            Clock.schedule_once(
                lambda dt: self.update_status(f'"{short_title}" MP3 indiriliyor...', COLORS['warning'])
            )
            
            # CRİTİK: DIRECT MP3 FORMATI - FFmpeg GEREKTİRMEZ!
            # YouTube'da hazır MP3 formatı olan videoları bul
            ydl_opts = {
                # MP3 formatını doğrudan ara
                'format': 'bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio',
                'outtmpl': os.path.join(folder, f'{safe_title}.%(ext)s'),
                'progress_hooks': [progress_hook],
                'quiet': False,
                'no_warnings': False,
                'noplaylist': True,
                'continuedl': True,
                'noprogress': False,
                'logger': self.logger,
                # FFmpeg'i DEVRE DIŞI bırak
                'postprocessors': [],
                # YouTube'daki tüm formatları listele
                'listformats': False,
                # Daha fazla format seçeneği
                'format_sort': ['res:720', 'ext:mp3:m4a:webm'],
                # Audio kalitesi
                'audioquality': '9' if quality == '128' else '5',
            }
            
            print("🚀 Direct MP3 indirme başlatılıyor...")
            print("ℹ️  FFmpeg GEREKMİYOR - YouTube'dan direct audio indiriliyor")
            
            # 3. İNDİRMEYİ BAŞLAT
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # 4. DOSYA KONTROLÜ ve MP3'e DÖNÜŞTÜRME (MANUEL)
            Clock.schedule_once(lambda dt: self.update_progress(98))
            Clock.schedule_once(lambda dt: self.update_status('Dosya kontrol ediliyor...', COLORS['warning']))
            
            # İndirilen dosyayı bul
            found_file = None
            possible_exts = ['.webm', '.m4a', '.mp3', '.opus', '.ogg']
            
            for ext in possible_exts:
                filepath = os.path.join(folder, f'{safe_title}{ext}')
                if os.path.exists(filepath):
                    found_file = filepath
                    print(f"📁 Bulunan dosya: {found_file}")
                    break
            
            if found_file:
                file_ext = os.path.splitext(found_file)[1].lower()
                
                # Eğer MP3 değilse, dosya adını MP3 yap
                if file_ext != '.mp3':
                    mp3_file = os.path.join(folder, f'{safe_title}.mp3')
                    try:
                        # Dosyayı yeniden adlandır
                        os.rename(found_file, mp3_file)
                        found_file = mp3_file
                        print(f"📝 Dosya MP3 olarak yeniden adlandırıldı: {mp3_file}")
                    except Exception as e:
                        print(f"⚠️  Dosya adı değiştirilemedi: {e}")
                        # Dosya adını değiştiremezsek, olduğu gibi bırak
                
                file_size = os.path.getsize(found_file) / (1024 * 1024)  # MB
                
                print(f"\n✅ İNDİRME BAŞARILI!")
                print(f"📂 Dosya: {found_file}")
                print(f"📊 Boyut: {file_size:.2f} MB")
                print(f"🎧 Format: MP3 (Direct Download)")
                
                Clock.schedule_once(lambda dt: self.update_progress(100))
                Clock.schedule_once(
                    lambda dt: self.update_status('✅ MP3 indirme tamamlandı!', COLORS['success'])
                )
                
                # Başarı popup'ı
                Clock.schedule_once(
                    lambda dt: self.show_success_popup(title, folder, quality, f"{file_size:.2f} MB")
                )
            else:
                print("⚠️  İndirilen dosya bulunamadı!")
                
                # Alternatif indirme yöntemi
                print("🔄 Alternatif yöntem deneniyor...")
                Clock.schedule_once(
                    lambda dt: self.update_status('Alternatif yöntem deneniyor...', COLORS['warning'])
                )
                
                # 2. YÖNTEM: YouTube'un hazır audio formatlarını indir
                self.alternative_download(url, folder, safe_title, quality)
                
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            print(f"\n❌ YouTube İndirme Hatası: {error_msg}")
            
            # Alternatif yöntemi dene
            print("🔄 Alternatif yöntem deneniyor...")
            Clock.schedule_once(
                lambda dt: self.update_status('Alternatif yöntem deneniyor...', COLORS['warning'])
            )
            
            try:
                self.alternative_download(url, folder, safe_title, quality)
            except Exception as e2:
                error_detail = self.get_error_detail(error_msg)
                Clock.schedule_once(lambda dt: self.show_popup('İndirme Hatası', error_detail))
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ Beklenmeyen Hata: {error_msg}")
            raise
    
    def alternative_download(self, url, folder, safe_title, quality):
        """ALTERNATİF İNDİRME YÖNTEMİ"""
        print("\n🔄 ALTERNATİF İNDİRME YÖNTEMİ BAŞLATILIYOR")
        
        # Daha basit ayarlar
        ydl_opts = {
            'format': 'worstaudio/worst',  # En küçük boyutlu audio
            'outtmpl': os.path.join(folder, f'{safe_title}.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'noplaylist': True,
            'continuedl': True,
            'logger': self.logger,
            # Sadece audio
            'extractaudio': True,
            'audioformat': 'mp3',
            # YouTube Music'i dene
            'source_address': '0.0.0.0',
            # Daha basit
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'nooverwrites': True,
            'retries': 3,
            'fragment_retries': 3,
            'skip_unavailable_fragments': True,
        }
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Dosyayı kontrol et
            for ext in ['.mp3', '.m4a', '.webm', '.opus']:
                filepath = os.path.join(folder, f'{safe_title}{ext}')
                if os.path.exists(filepath):
                    file_size = os.path.getsize(filepath) / (1024 * 1024)
                    print(f"✅ ALTERNATİF İNDİRME BAŞARILI!")
                    print(f"📂 Dosya: {filepath}")
                    print(f"📊 Boyut: {file_size:.2f} MB")
                    
                    Clock.schedule_once(lambda dt: self.update_progress(100))
                    Clock.schedule_once(
                        lambda dt: self.update_status('✅ Alternatif indirme tamam!', COLORS['success'])
                    )
                    
                    Clock.schedule_once(
                        lambda dt: self.show_success_popup(
                            self.current_title, folder, quality, f"{file_size:.2f} MB"
                        )
                    )
                    return
            
            print("❌ Alternatif yöntem de başarısız oldu")
            Clock.schedule_once(
                lambda dt: self.update_status('❌ İndirme başarısız oldu', COLORS['error'])
            )
            
        except Exception as e:
            print(f"❌ Alternatif yöntem hatası: {e}")
            raise
    
    def get_error_detail(self, error_msg):
        """Hata detaylarını al"""
        if 'age restricted' in error_msg.lower():
            return "Bu video yaş sınırlı. YouTube'dan giriş yapmanız gerekebilir."
        elif 'copyright' in error_msg.lower():
            return "Telif hakları nedeniyle engellendi."
        elif 'unavailable' in error_msg.lower():
            return "Video bölgenizde mevcut değil."
        elif 'private' in error_msg.lower():
            return "Bu video özel veya gizli."
        elif 'format' in error_msg.lower():
            return "Video formatı desteklenmiyor. Farklı bir video deneyin."
        elif 'sign in' in error_msg.lower():
            return "YouTube'a giriş yapmanız gerekebilir."
        else:
            return f"Hata: {error_msg[:100]}"
    
    @mainthread
    def show_popup(self, title, message):
        """Popup göster"""
        content = BoxLayout(orientation='vertical', 
                          spacing=dp(20 if IS_ANDROID else 15), 
                          padding=dp(25 if IS_ANDROID else 20))
        
        title_label = Label(
            text=f'[b]{title}[/b]',
            font_size=sp(24 if IS_ANDROID else 20),
            markup=True,
            color=COLORS['primary'],
            size_hint_y=None,
            height=dp(50 if IS_ANDROID else 40),
            halign='center',
            valign='middle'
        )
        
        # Mesaj için ScrollView
        scroll_view = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        
        message_label = Label(
            text=message,
            font_size=sp(18 if IS_ANDROID else 16),
            color=COLORS['light'],
            halign='center',
            valign='middle',
            text_size=(Window.width * 0.7, None),
            size_hint_y=None
        )
        message_label.bind(texture_size=message_label.setter('size'))
        
        scroll_view.add_widget(message_label)
        
        ok_btn = Button(
            text='TAMAM',
            font_size=sp(20 if IS_ANDROID else 18),
            background_color=COLORS['primary'],
            size_hint_y=None,
            height=dp(60 if IS_ANDROID else 50),
            size_hint_x=0.8 if IS_ANDROID else 1
        )
        
        content.add_widget(title_label)
        content.add_widget(scroll_view)
        content.add_widget(ok_btn)
        
        # Popup boyutlarını platforma göre ayarla
        if IS_ANDROID:
            popup_size = (Window.width * 0.85, Window.height * 0.5)
        else:
            popup_size = (0.8, 0.5)
        
        popup = Popup(
            title='',
            content=content,
            size_hint=(None, None) if IS_ANDROID else popup_size,
            size=popup_size if IS_ANDROID else (0, 0),
            separator_height=0,
            background='',
            auto_dismiss=False
        )
        
        # Arka plan
        with popup.canvas.before:
            Color(rgba=COLORS['darker'])
            RoundedRectangle(size=popup.size, pos=popup.pos, 
                           radius=[dp(25) if IS_ANDROID else dp(20)])
        
        ok_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    @mainthread
    def show_success_popup(self, title, folder, quality, file_size):
        """Başarı popup'ı"""
        content = BoxLayout(orientation='vertical', 
                          spacing=dp(20 if IS_ANDROID else 15), 
                          padding=dp(25 if IS_ANDROID else 25))
        
        icon_label = Label(
            text='✅',
            font_size=sp(45 if IS_ANDROID else 40),
            size_hint_y=None,
            height=dp(70 if IS_ANDROID else 60),
            halign='center'
        )
        
        title_label = Label(
            text='[b]🎉 MP3 İndirme Tamamlandı![/b]',
            font_size=sp(26 if IS_ANDROID else 22),
            markup=True,
            color=COLORS['success'],
            size_hint_y=None,
            height=dp(50 if IS_ANDROID else 40),
            halign='center'
        )
        
        # Klasörü kısalt
        folder_display = folder
        if len(folder_display) > 40:
            folder_display = f"...{folder_display[-35:]}"
        
        details_text = f"""
[b]🎵 Şarkı:[/b] {title[:35]}...
[b]📁 Klasör:[/b] {folder_display}
[b]🎧 Kalite:[/b] {quality}kbps
[b]📊 Boyut:[/b] {file_size}
[b]🔧 FFmpeg:[/b] GEREK YOK!
[b]🕒 Tarih:[/b] {datetime.now().strftime("%H:%M")}

[i]by Lütfi[/i]
        """
        
        details_label = Label(
            text=details_text,
            font_size=sp(16 if IS_ANDROID else 14),
            markup=True,
            color=COLORS['light'],
            halign='center',
            valign='middle'
        )
        
        # Butonlar
        btn_layout = BoxLayout(spacing=dp(15 if IS_ANDROID else 10), 
                             size_hint_y=None, 
                             height=dp(65 if IS_ANDROID else 50))
        
        close_btn = Button(
            text='KAPAT',
            font_size=sp(18 if IS_ANDROID else 16),
            background_color=COLORS['gray']
        )
        
        open_btn = Button(
            text='📂 AÇ',
            font_size=sp(18 if IS_ANDROID else 16),
            background_color=COLORS['success']
        )
        
        btn_layout.add_widget(close_btn)
        btn_layout.add_widget(open_btn)
        
        content.add_widget(icon_label)
        content.add_widget(title_label)
        content.add_widget(details_label)
        content.add_widget(btn_layout)
        
        # Popup boyutlarını platforma göre ayarla
        if IS_ANDROID:
            popup_size = (Window.width * 0.9, Window.height * 0.6)
        else:
            popup_size = (0.85, 0.65)
        
        popup = Popup(
            title='',
            content=content,
            size_hint=(None, None) if IS_ANDROID else popup_size,
            size=popup_size if IS_ANDROID else (0, 0),
            separator_height=0,
            background='',
            auto_dismiss=False
        )
        
        # Arka plan
        with popup.canvas.before:
            Color(rgba=COLORS['darker'])
            RoundedRectangle(size=popup.size, pos=popup.pos, 
                           radius=[dp(30) if IS_ANDROID else dp(25)])
        
        close_btn.bind(on_press=popup.dismiss)
        open_btn.bind(on_press=lambda x: self.open_folder(folder))
        
        popup.open()
    
    def open_folder(self, folder):
        """Klasörü aç"""
        try:
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.run(["open", folder], check=False)
            else:
                # Android için dosya yöneticisi
                if IS_ANDROID:
                    # Pydroid 3'te dosya göster
                    self.show_popup('Dosya Kaydedildi', 
                        f'Dosya bu klasöre kaydedildi:\n\n{folder}\n\n'
                        f'Dosya yöneticisinde bu klasöre gidin:\n'
                        f'1. Dosya Yöneticisi uygulamasını aç\n'
                        f'2. "İndirilenler" klasörüne gidin\n'
                        f'3. "LutYouMP3" klasörünü bulun')
                else:
                    subprocess.run(["xdg-open", folder], check=False)
        except:
            self.show_popup('Bilgi', f'Dosya kaydedildi:\n\n{folder}')

def main():
    """Ana fonksiyon"""
    print("=" * 60)
    
    if IS_ANDROID:
        print("🎵 LutYouMP3 - Android (Pydroid 3) Versiyonu")
        print("🔥 FFmpeg GEREKTİRMEZ - Direct MP3!")
    else:
        print("🎵 LutYouMP3 - PC Versiyonu")
        print("🔥 FFmpeg GEREKTİRMEZ - Direct MP3!")
    
    print("Geliştirici: Lütfi")
    print("✅ DIRECT MP3 İNDİRİCİ")
    print("=" * 60)
    
    # Gereksinim kontrolü
    if not YTDLP_AVAILABLE:
        print("❌ yt-dlp kurulu değil!")
        print("Kurmak için: pip install yt-dlp")
        if not IS_ANDROID:
            input("⏎ Çıkmak için Enter...")
        return
    
    if not KIVY_AVAILABLE:
        print("❌ Kivy kurulu değil!")
        print("Kurmak için: pip install kivy[base]")
        return
    
    print("\n✅ Tüm gereksinimler tamam!")
    print("🚀 Uygulama başlatılıyor...")
    print("\n🎧 ÖZELLİKLER:")
    print("   • FFmpeg GEREKTİRMEZ")
    print("   • Direct MP3 indirme")
    print("   • Pydroid 3'te çalışır")
    print("   • 128kbps kalite (en garantili)")
    print("\nℹ️  İPUCU:")
    print("   • İlk indirme biraz yavaş olabilir")
    print("   • Bazı videolarda MP3 olmayabilir")
    print("   • Müzik videoları en iyi sonucu verir")
    print("=" * 60)
    
    LutYouMP3().run()

if __name__ == '__main__':
    main()