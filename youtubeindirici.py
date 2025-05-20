import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from threading import Thread
from yt_dlp import YoutubeDL

class VideoDownloaderApp:
    """YouTube videoları indirmek için GUI uygulaması."""

    def __init__(self, root):
        """Ana pencereyi ve bileşenleri başlatır."""
        self.root = root
        self.root.title("YouTube Video İndirici")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f2f5")  # Hafif gri arka plan

        # Varsayılan indirme yolu
        self.downloads_path = os.path.join(os.path.expanduser("~"), "Desktop")
        self.downloaded_videos = []

        self.create_widgets()

    def create_widgets(self):
        """Arayüz bileşenlerini oluşturur."""
        style = ttk.Style()
        style.theme_use('clam')  # Daha modern bir tema seçiyoruz

        style.configure("TButton",
                        font=("Helvetica", 12),
                        background="#4CAF50",
                        foreground="white",
                        padding=10)

        style.map("TButton",
                  background=[('active', '#45a049')])

        style.configure("TCombobox",
                        font=("Helvetica", 11))

        # Başlık
        self.title_label = tk.Label(self.root, text="YouTube Video/Ses İndirici", 
                                    font=("Helvetica", 18, "bold"), bg="#f0f2f5", fg="#333")
        self.title_label.pack(pady=20)

        # URL Girişi
        self.url_label = tk.Label(self.root, text="Video Linki:", font=("Helvetica", 12), bg="#f0f2f5")
        self.url_label.pack(pady=5)

        self.url_entry = tk.Entry(self.root, width=60, font=("Helvetica", 11))
        self.url_entry.pack(pady=5)

        # Kalite Seçimi
        self.quality_label = tk.Label(self.root, text="Ne indirmek istiyorsun?", font=("Helvetica", 12), bg="#f0f2f5")
        self.quality_label.pack(pady=10)

        self.quality_var = tk.StringVar(value="video")
        self.quality_combobox = ttk.Combobox(
            self.root,
            textvariable=self.quality_var,
            values=["video", "ses"],
            state="readonly",
            width=20
        )
        self.quality_combobox.pack(pady=5)

        # İndir Butonu
        self.download_button = ttk.Button(
            self.root, text="İndir", command=self.start_download_thread
        )
        self.download_button.pack(pady=15)

        # Klasör Seç Butonu
        self.folder_button = ttk.Button(
            self.root, text="Klasör Seç", command=self.select_download_folder
        )
        self.folder_button.pack(pady=10)

        # İndirme Durumu
        self.status_text = tk.StringVar()
        self.status_label = tk.Label(self.root, textvariable=self.status_text, font=("Helvetica", 10), bg="#f0f2f5", fg="#555")
        self.status_label.pack(pady=5)

        # İlerleme Çubuğu
        self.progress = ttk.Progressbar(
            self.root, orient="horizontal", length=400, mode="determinate"
        )
        self.progress.pack(pady=10)

        # İndirilenler Listesi
        self.list_label = tk.Label(self.root, text="İndirilenler:", font=("Helvetica", 12, "bold"), bg="#f0f2f5")
        self.list_label.pack(pady=5)

        self.video_listbox = tk.Listbox(self.root, width=60, font=("Helvetica", 10))
        self.video_listbox.pack(pady=5, expand=True)

    def select_download_folder(self):
        """Kullanıcının indirme klasörünü seçmesini sağlar."""
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.downloads_path = folder_selected
            self.update_status(f"İndirme klasörü seçildi: {self.downloads_path}")

    def start_download_thread(self):
        """İndirme işlemini ayrı bir thread'de başlatır."""
        thread = Thread(target=self.download_video)
        thread.start()

    def download_video(self):
        """Video veya ses indirme işlemini yönetir."""
        url = self.url_entry.get().strip()
        if not url:
            self.safe_messagebox("warning", "Uyarı", "Lütfen bir video linki girin.")
            return

        selected_quality = self.quality_var.get()
        ydl_format = self.map_quality_to_format(selected_quality)

        self.update_status("İndirme başlatıldı...")
        self.progress['value'] = 0

        def progress_hook(d):
            """İndirme ilerlemesini güncelleyen iç fonksiyon."""
            if d['status'] == 'downloading':
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded_bytes = d.get('downloaded_bytes', 0)

                # Eğer total_bytes None ise, yüzdelik hesaplama yapılmaz
                if total_bytes:
                    percent = (downloaded_bytes / total_bytes) * 100
                    self.root.after(0, self.update_progress, percent)

                    speed = d.get('speed', 0)
                    eta = d.get('eta', 0)

                    self.root.after(0, self.update_status,
                        f"İndiriliyor: {percent:.2f}% | "
                        f"{downloaded_bytes / 1024 / 1024:.2f} MB / "
                        f"{(total_bytes or 1) / 1024 / 1024:.2f} MB | "
                        f"Hız: {speed / 1024:.2f} KB/s | ETA: {eta}s"
                    )

            elif d['status'] == 'finished':
                filename = d['info_dict'].get('title', 'Bilinmeyen')
                self.root.after(0, self.finish_download, filename)

        options = {
            'outtmpl': f'{self.downloads_path}/%(title)s.%(ext)s',
            'format': ydl_format,
            'progress_hooks': [progress_hook],
            'quiet': True,
        }

        try:
            with YoutubeDL(options) as ydl:
                ydl.download([url])
        except Exception as e:
            self.safe_messagebox("error", "Hata", f"İndirme sırasında hata oluştu:\n{e}")
            self.update_status("İndirme hatası!")

    def map_quality_to_format(self, quality):
        """Kalite seçimine göre yt-dlp formatı döner."""
        if quality == "video":
            return "best"
        elif quality == "ses":
            return "bestaudio"
        else:
            return "best"

    def update_status(self, message):
        """Durum metnini günceller."""
        self.status_text.set(message)

    def update_progress(self, percent):
        """İlerleme çubuğunu günceller."""
        self.progress['value'] = percent

    def finish_download(self, filename):
        """İndirme tamamlandığında yapılacak işlemler."""
        self.update_status("İndirme tamamlandı!")
        self.video_listbox.insert(tk.END, filename)
        self.downloaded_videos.append(filename)

    def safe_messagebox(self, type_, title, message):
        """Thread güvenliği için tkinter mesaj kutularını güvenli şekilde gösterir."""
        if type_ == "warning":
            self.root.after(0, lambda: messagebox.showwarning(title, message))
        elif type_ == "error":
            self.root.after(0, lambda: messagebox.showerror(title, message))


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoDownloaderApp(root)
    root.mainloop()
    