# main.py - Uygulamanın giriş noktası; tkinter ile profesyonel GUI arayüzü

import tkinter as tk                    # Standart Python GUI kütüphanesi
from tkinter import ttk, messagebox    # Tablo widgetı ve mesaj kutusu
import threading                        # Arka planda veri toplama için
import time                             # Güncelleme aralığı kontrolü

# Kendi modüllerimizi import et (modüler yapı)
from monitor  import CPUMonitor, GPUMonitor, RAMMonitor, FPSMonitor, DiskMonitor
from analyzer import SystemAnalyzer    # Değerlendirme mantığı


# ───────────────────────────────────────────────
# ANA UYGULAMA SINIFI
# ───────────────────────────────────────────────
class GameMonitorApp:
    """Tüm GUI ve iş mantığını yöneten ana uygulama sınıfı."""

    # Renk paleti — koyu oyun teması
    COLORS = {
        "bg"      : "#0d1117",   # Arka plan (derin siyah)
        "card"    : "#161b22",   # Kart arka planı
        "border"  : "#30363d",   # Kenarlık rengi
        "accent"  : "#58a6ff",   # Ana vurgu rengi (mavi)
        "green"   : "#3fb950",   # İyi durum rengi
        "yellow"  : "#d29922",   # Uyarı rengi
        "orange"  : "#f0883e",   # Orta durum rengi
        "red"     : "#f85149",   # Kritik durum rengi
        "text"    : "#e6edf3",   # Ana metin rengi
        "subtext" : "#8b949e",   # İkincil metin rengi
    }

    def __init__(self, root: tk.Tk):
        self._root = root                  # Tkinter ana pencere
        self._running = False              # İzleme aktif mi?
        self._thread  = None              # Arka plan iş parçacığı

        # Monitör nesneleri oluştur (OOP — her biri kendi sınıfından)
        self._cpu   = CPUMonitor()
        self._gpu   = GPUMonitor()
        self._ram   = RAMMonitor()
        self._fps   = FPSMonitor()
        self._disk  = DiskMonitor()
        self._analyzer = SystemAnalyzer() # Analiz motoru

        self._setup_window()   # Pencere ayarları
        self._build_ui()       # Arayüz elemanlarını oluştur

    # ── Pencere temel ayarları ──
    def _setup_window(self):
        self._root.title("🎮 GameMonitor — Sistem İzleme Aracı")
        self._root.configure(bg=self.COLORS["bg"])
        self._root.geometry("920x680")        # Başlangıç boyutu
        self._root.minsize(860, 600)           # Minimum pencere boyutu
        self._root.resizable(True, True)       # Yeniden boyutlandırılabilir

    # ── Tüm arayüzü inşa et ──
    def _build_ui(self):
        self._build_header()    # Üst başlık bandı
        self._build_cards()     # Metrik kartları
        self._build_score()     # Genel skor alanı
        self._build_table()     # Geçmiş veri tablosu
        self._build_controls()  # Alt kontrol düğmeleri

    # ── Üst başlık ──
    def _build_header(self):
        hdr = tk.Frame(self._root, bg=self.COLORS["card"], pady=12)
        hdr.pack(fill="x")                         # Yatay olarak genişlet
        tk.Label(hdr, text="🎮  GAME MONITOR",
                 font=("Segoe UI", 18, "bold"),
                 fg=self.COLORS["accent"], bg=self.COLORS["card"]).pack(side="left", padx=20)
        self._status_lbl = tk.Label(hdr, text="● Bekleniyor",
                                     font=("Segoe UI", 11),
                                     fg=self.COLORS["subtext"], bg=self.COLORS["card"])
        self._status_lbl.pack(side="right", padx=20)  # Durum göstergesi sağda

    # ── Metrik kartları ──
    def _build_cards(self):
        frame = tk.Frame(self._root, bg=self.COLORS["bg"], pady=10)
        frame.pack(fill="x", padx=15)

        # Her kart: (başlık, ikon, renk değişkeni adı)
        card_defs = [
            ("FPS"          , "🎯", "fps_val"  ),
            ("CPU Kullanım" , "🖥", "cpu_val"  ),
            ("CPU Sıcaklık" , "🌡", "cput_val" ),
            ("GPU Kullanım" , "🎮", "gpu_val"  ),
            ("GPU Sıcaklık" , "🌡", "gput_val" ),
            ("RAM Kullanım" , "💾", "ram_val"  ),
            ("Disk I/O"     , "💿", "disk_val" ),
        ]

        self._card_vars = {}    # Kart StringVar'larını sakla
        for i, (title, icon, key) in enumerate(card_defs):
            var = tk.StringVar(value="--")       # Başlangıç değeri
            self._card_vars[key] = var
            self._make_card(frame, icon, title, var, i)

    def _make_card(self, parent, icon, title, var, col):
        """Tek bir metrik kartı oluşturur."""
        card = tk.Frame(parent, bg=self.COLORS["card"],
                        relief="flat", bd=0, padx=8, pady=8)
        card.grid(row=0, column=col, padx=5, sticky="ew")
        parent.columnconfigure(col, weight=1)   # Eşit genişlik dağılımı

        tk.Label(card, text=icon, font=("Segoe UI", 16),
                 bg=self.COLORS["card"], fg=self.COLORS["accent"]).pack()
        tk.Label(card, text=title, font=("Segoe UI", 8),
                 bg=self.COLORS["card"], fg=self.COLORS["subtext"]).pack()
        tk.Label(card, textvariable=var, font=("Consolas", 13, "bold"),
                 bg=self.COLORS["card"], fg=self.COLORS["text"]).pack()

    # ── Genel skor alanı ──
    def _build_score(self):
        sf = tk.Frame(self._root, bg=self.COLORS["bg"])
        sf.pack(fill="x", padx=15, pady=(0, 6))

        score_card = tk.Frame(sf, bg=self.COLORS["card"], pady=10)
        score_card.pack(fill="x")

        tk.Label(score_card, text="GENEL PERFORMANS SKORU",
                 font=("Segoe UI", 9, "bold"),
                 fg=self.COLORS["subtext"], bg=self.COLORS["card"]).pack()

        self._score_var   = tk.StringVar(value="—")       # Anlık skor metni
        self._verdict_var = tk.StringVar(value="İzleme başlatılmadı")  # Karar metni

        tk.Label(score_card, textvariable=self._score_var,
                 font=("Consolas", 28, "bold"),
                 fg=self.COLORS["accent"], bg=self.COLORS["card"]).pack()
        tk.Label(score_card, textvariable=self._verdict_var,
                 font=("Segoe UI", 11),
                 fg=self.COLORS["text"], bg=self.COLORS["card"]).pack()

        # İlerleme çubuğu için özel ttk stili
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Score.Horizontal.TProgressbar",
                        troughcolor=self.COLORS["border"],
                        background=self.COLORS["accent"],
                        thickness=14)
        self._progress = ttk.Progressbar(score_card, style="Score.Horizontal.TProgressbar",
                                          orient="horizontal", length=500, maximum=100)
        self._progress.pack(pady=6)       # Skor çubuğunu pakete ekle

    # ── Geçmiş tablosu ──
    def _build_table(self):
        tf = tk.Frame(self._root, bg=self.COLORS["bg"])
        tf.pack(fill="both", expand=True, padx=15, pady=(0, 8))

        cols = ("Saat", "FPS", "CPU%", "CPU°C", "GPU%", "GPU°C", "RAM%", "Skor", "Durum")
        self._tree = ttk.Treeview(tf, columns=cols, show="headings", height=8)

        # Her sütunu yapılandır
        widths = (70, 55, 55, 60, 55, 60, 55, 55, 140)
        for col, w in zip(cols, widths):
            self._tree.heading(col, text=col)
            self._tree.column (col, width=w, anchor="center")

        # Treeview renk teması
        ts = ttk.Style()
        ts.configure("Treeview",
                     background=self.COLORS["card"],
                     foreground=self.COLORS["text"],
                     fieldbackground=self.COLORS["card"],
                     rowheight=24, font=("Consolas", 9))
        ts.configure("Treeview.Heading",
                     background=self.COLORS["border"],
                     foreground=self.COLORS["text"],
                     font=("Segoe UI", 9, "bold"))
        ts.map("Treeview", background=[("selected", self.COLORS["accent"])])

        # Dikey kaydırma çubuğu
        sb = ttk.Scrollbar(tf, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    # ── Alt kontrol butonları ──
    def _build_controls(self):
        cf = tk.Frame(self._root, bg=self.COLORS["bg"], pady=8)
        cf.pack(fill="x", padx=15)

        btn_cfg = dict(font=("Segoe UI", 10, "bold"), relief="flat",
                       padx=18, pady=7, cursor="hand2", bd=0)

        self._start_btn = tk.Button(cf, text="▶  İzlemeyi Başlat",
                                     bg=self.COLORS["green"], fg="#000",
                                     command=self._start, **btn_cfg)
        self._start_btn.pack(side="left", padx=(0, 8))

        self._stop_btn = tk.Button(cf, text="■  Durdur",
                                    bg=self.COLORS["red"], fg="#fff",
                                    command=self._stop, state="disabled", **btn_cfg)
        self._stop_btn.pack(side="left", padx=(0, 8))

        tk.Button(cf, text="🗑  Tabloyu Temizle",
                  bg=self.COLORS["border"], fg=self.COLORS["text"],
                  command=self._clear_table, **btn_cfg).pack(side="left", padx=(0, 8))

        tk.Button(cf, text="📊  Oturum Özeti",
                  bg=self.COLORS["accent"], fg="#000",
                  command=self._show_summary, **btn_cfg).pack(side="right")

    # ───────────────────────────────────────────
    # KONTROL METODLARı
    # ───────────────────────────────────────────
    def _start(self):
        """İzlemeyi başlatır; arka plan iş parçacığı oluşturur."""
        if self._running:
            return                               # Zaten çalışıyorsa işlem yapma
        self._running = True
        self._start_btn.config(state="disabled") # Başlat butonunu pasifleştir
        self._stop_btn .config(state="normal")   # Durdur butonunu aktifleştir
        self._status_lbl.config(text="● İzleniyor", fg=self.COLORS["green"])
        self._thread = threading.Thread(target=self._loop, daemon=True)  # Daemon thread
        self._thread.start()                     # İş parçacığını başlat

    def _stop(self):
        """İzlemeyi durdurur."""
        self._running = False                    # Döngü bayrağını kapat
        self._start_btn.config(state="normal")
        self._stop_btn .config(state="disabled")
        self._status_lbl.config(text="● Durduruldu", fg=self.COLORS["yellow"])

    def _clear_table(self):
        """Tablodaki tüm satırları siler."""
        for item in self._tree.get_children():
            self._tree.delete(item)

    def _show_summary(self):
        """Oturum özeti bilgi kutusunu gösterir."""
        s = self._analyzer.session_summary()
        if not s:
            messagebox.showinfo("Özet", "Henüz yeterli veri toplanmadı.")
            return
        msg = (f"Ortalama Skor : {s['avg_score']}\n"
               f"En Düşük Skor: {s['min_score']}\n"
               f"En Yüksek Skor: {s['max_score']}\n"
               f"Toplam Örnek : {s['samples']}\n\n"
               f"Değerlendirme: {s['verdict']}")
        messagebox.showinfo("📊 Oturum Özeti", msg)

    # ───────────────────────────────────────────
    # ARKA PLAN VERİ DÖNGÜSÜ
    # ───────────────────────────────────────────
    def _loop(self):
        """Her 1 saniyede veri toplar; GUI'yi ana thread üzerinden günceller."""
        while self._running:
            cpu  = self._cpu .collect()   # CPU verisi
            gpu  = self._gpu .collect()   # GPU verisi
            ram  = self._ram .collect()   # RAM verisi
            fps  = self._fps .collect()   # FPS verisi
            disk = self._disk.collect()   # Disk verisi

            # Anlık veri sözlüğü (analyzer için düzleştirilmiş)
            snap = {
                "fps"       : fps ["fps"        ],
                "cpu_usage" : cpu ["usage"       ],
                "cpu_temp"  : cpu ["temperature" ],
                "gpu_usage" : gpu ["usage"       ],
                "gpu_temp"  : gpu ["temperature" ],
                "ram_usage" : ram ["usage"       ],
                "disk_usage": disk["usage"       ],
            }
            result = self._analyzer.evaluate(snap)  # Analiz et

            # GUI güncellemesini ana thread'e ilet (tkinter thread-safe değil)
            self._root.after(0, self._update_ui, snap, result)
            time.sleep(1)   # 1 saniye bekle

    def _update_ui(self, snap: dict, result: dict):
        """Ana thread'de çalışır; tüm widget değerlerini günceller."""
        # Kart değerlerini güncelle
        self._card_vars["fps_val" ].set(f"{snap['fps']:.0f} FPS")
        self._card_vars["cpu_val" ].set(f"{snap['cpu_usage']:.0f}%")
        self._card_vars["cput_val"].set(f"{snap['cpu_temp']:.1f}°C")
        self._card_vars["gpu_val" ].set(f"{snap['gpu_usage']:.0f}%")
        self._card_vars["gput_val"].set(f"{snap['gpu_temp']:.1f}°C")
        self._card_vars["ram_val" ].set(f"{snap['ram_usage']:.0f}%")

        disk = self._disk.history[-1] if self._disk.history else {}
        self._card_vars["disk_val"].set(
            f"R:{disk.get('read_mb',0):.1f} W:{disk.get('write_mb',0):.1f}")

        # Genel skor alanını güncelle
        score = result["overall"]
        self._score_var  .set(f"{score:.0f} / 100")
        self._verdict_var.set(result["verdict"])
        self._progress["value"] = score              # İlerleme çubuğu

        # Skora göre renk değiştir
        color = (self.COLORS["green"]  if score >= 85 else
                 self.COLORS["yellow"] if score >= 65 else
                 self.COLORS["orange"] if score >= 40 else
                 self.COLORS["red"])
        self._score_var_lbl_color(color)

        # Tabloya yeni satır ekle
        ts   = self._cpu.history[-1].get("timestamp", "--") if self._cpu.history else "--"
        row  = (ts,
                f"{snap['fps']:.0f}",
                f"{snap['cpu_usage']:.0f}",
                f"{snap['cpu_temp']:.1f}",
                f"{snap['gpu_usage']:.0f}",
                f"{snap['gpu_temp']:.1f}",
                f"{snap['ram_usage']:.0f}",
                f"{score:.0f}",
                result["verdict"].split(" ", 1)[-1])   # Emojisiz kısa metin
        self._tree.insert("", 0, values=row)           # En üste ekle

        # Tablo 100 satırı geçerse en altındaki sil
        children = self._tree.get_children()
        if len(children) > 100:
            self._tree.delete(children[-1])

    def _score_var_lbl_color(self, color: str):
        """Skor etiketinin ön plan rengini değiştirir."""
        for widget in self._root.winfo_children():
            self._find_label(widget, self._score_var, color)

    def _find_label(self, widget, var, color):
        """Verilen StringVar'a bağlı Label'ı bulur ve rengini ayarlar."""
        try:
            if isinstance(widget, tk.Label) and widget.cget("textvariable") == str(var):
                widget.config(fg=color)
        except Exception:
            pass
        for child in widget.winfo_children():  # Alt widget'ları da tara
            self._find_label(child, var, color)


# ───────────────────────────────────────────────
# UYGULAMA GİRİŞ NOKTASI
# ───────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()                  # Tkinter ana pencereyi oluştur
    app  = GameMonitorApp(root)     # Uygulama nesnesini başlat
    root.mainloop()                 # GUI olay döngüsünü başlat
