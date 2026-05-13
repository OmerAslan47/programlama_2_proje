# =============================================================================
# main.py - Ana Çalışma Dosyası (GUI dahil)
# Kastamonu Üniversitesi Tosya MYO - Programlama II Dönem Projesi
# Tkinter ile profesyonel karanlık tema arayüz sunar.
# =============================================================================

import tkinter as tk                       # Tkinter: Python yerleşik GUI kütüphanesi
from tkinter import ttk, messagebox        # ttk: gelişmiş widget'lar; messagebox: diyaloglar
import threading                           # Arka planda veri toplama için
import time                                # Bekleme (sleep) için
from datetime import datetime              # Tarih/saat işlemleri

# Kendi modüllerimizi import et (modüler yapı)
from monitor import SensorGroup, GameProfileManager   # Sensör ve profil sınıfları
from analyzer import SystemEvaluator, AlertManager, ReportGenerator  # Analiz sınıfları


# =============================================================================
# RENK PALETİ - Karanlık tema sabitleri (merkezi renk yönetimi)
# =============================================================================
class ColorPalette:
    """Tüm arayüz renklerini merkezi olarak yöneten sabit sınıf."""

    # Arka plan renkleri
    BG_DARK = "#0D0F1A"                   # Ana koyu arka plan
    BG_CARD = "#161928"                   # Kart arka planı
    BG_PANEL = "#1E2235"                  # Panel arka planı
    BG_HEADER = "#0A0C15"                 # Başlık çubuğu

    # Aksan renkleri (neon tonu)
    ACCENT_CYAN = "#00F5FF"               # Cyan vurgu
    ACCENT_GREEN = "#39FF14"              # Neon yeşil (iyi durum)
    ACCENT_YELLOW = "#FFD700"             # Altın sarısı (uyarı)
    ACCENT_RED = "#FF3131"                # Parlak kırmızı (kritik)
    ACCENT_PURPLE = "#BF5FFF"             # Mor (ikincil bilgi)
    ACCENT_ORANGE = "#FF6B35"             # Turuncu (yüksek değer)

    # Metin renkleri
    TEXT_PRIMARY = "#E8EAF6"              # Birincil metin (açık gri)
    TEXT_SECONDARY = "#7986CB"            # İkincil metin (koyu mavi)
    TEXT_DIM = "#424A6B"                  # Soluk metin

    # Durum renkleri (değer aralığına göre)
    STATUS_GOOD = "#39FF14"               # İyi: neon yeşil
    STATUS_WARN = "#FFD700"               # Uyarı: sarı
    STATUS_BAD = "#FF6B35"                # Kötü: turuncu
    STATUS_CRIT = "#FF3131"               # Kritik: kırmızı


# =============================================================================
# METRİK KARTI BİLEŞENİ - Tek bir metriği gösteren UI bileşeni
# =============================================================================
class MetricCard:
    """Tek bir metriği gösteren kart widget'ı (OOP bileşeni)."""

    def __init__(self, parent, title: str, unit: str, col: int, row: int, col_span: int = 1):
        self._title = title               # Kartın başlığı
        self._unit = unit                 # Değerin birimi

        # Dış çerçeve (kart konteyneri)
        self._frame = tk.Frame(
            parent,
            bg=ColorPalette.BG_CARD,      # Kart arka plan rengi
            relief="flat",                # Düz kenarlık stili
            bd=0                          # Kenarlık kalınlığı: 0
        )
        self._frame.grid(
            row=row, column=col,
            columnspan=col_span,
            padx=6, pady=5,
            sticky="nsew"                 # Tüm yönlere genişle
        )

        # İç çerçeve (padding için)
        inner = tk.Frame(self._frame, bg=ColorPalette.BG_CARD)
        inner.pack(fill="both", expand=True, padx=12, pady=10)

        # Başlık etiketi
        tk.Label(
            inner,
            text=title.upper(),           # Büyük harfle göster
            font=("Courier New", 7, "bold"),
            fg=ColorPalette.TEXT_SECONDARY,
            bg=ColorPalette.BG_CARD
        ).pack(anchor="w")               # Sola hizala

        # Ana değer etiketi (büyük sayı)
        self._value_label = tk.Label(
            inner,
            text="---",                   # Başlangıç değeri
            font=("Courier New", 22, "bold"),
            fg=ColorPalette.ACCENT_CYAN,
            bg=ColorPalette.BG_CARD
        )
        self._value_label.pack(anchor="w")

        # Birim etiketi
        self._unit_label = tk.Label(
            inner,
            text=unit,
            font=("Courier New", 9),
            fg=ColorPalette.TEXT_DIM,
            bg=ColorPalette.BG_CARD
        )
        self._unit_label.pack(anchor="w")

        # Alt bilgi (durum metni)
        self._status_label = tk.Label(
            inner,
            text="",
            font=("Courier New", 8),
            fg=ColorPalette.TEXT_DIM,
            bg=ColorPalette.BG_CARD
        )
        self._status_label.pack(anchor="w")

        # İnce renkli alt çizgi (dekoratif)
        self._bar = tk.Frame(self._frame, bg=ColorPalette.ACCENT_CYAN, height=2)
        self._bar.pack(fill="x", side="bottom")

    def update(self, value, status_text: str = "", bar_color: str = None):
        """Kart değerini ve rengini güncelle."""
        # Değeri formatlı göster
        if isinstance(value, float):
            display = f"{value:.1f}"      # Tek ondalıklı göster
        else:
            display = str(value)

        # Değer rengini duruma göre ayarla
        color = bar_color or ColorPalette.ACCENT_CYAN
        self._value_label.config(text=display, fg=color)
        self._status_label.config(text=status_text, fg=color)
        self._bar.config(bg=color)       # Alt çizgi rengini de güncelle


# =============================================================================
# GRAFİK BİLEŞENİ - Canvas üzerinde mini çizgi grafik
# =============================================================================
class MiniChart:
    """Canvas üzerinde gerçek zamanlı çizgi grafik çizen bileşen."""

    def __init__(self, parent, title: str, color: str, max_val: float = 100):
        self._history = []                # Değer geçmişi (son N değer)
        self._max_val = max_val           # Y eksenindeki maksimum değer
        self._color = color               # Grafik çizgi rengi
        self._max_points = 60             # Kaç veri noktası gösterilsin

        # Kart çerçevesi
        frame = tk.Frame(parent, bg=ColorPalette.BG_CARD, bd=0)
        frame.pack(fill="x", padx=6, pady=4)

        # Başlık
        tk.Label(
            frame,
            text=title.upper(),
            font=("Courier New", 7, "bold"),
            fg=ColorPalette.TEXT_SECONDARY,
            bg=ColorPalette.BG_CARD
        ).pack(anchor="w", padx=10, pady=(8, 2))

        # Canvas (çizim alanı)
        self._canvas = tk.Canvas(
            frame,
            height=55,                    # Grafik yüksekliği
            bg="#0D1117",                 # Grafik arka planı (koyu lacivert)
            highlightthickness=0,         # Çerçeve kaldır
            bd=0
        )
        self._canvas.pack(fill="x", padx=10, pady=(0, 8))

    def add_value(self, value: float):
        """Yeni değer ekle ve grafiği yeniden çiz."""
        self._history.append(value)       # Listeye ekle

        # Maksimum nokta sayısını aşarsa en eskiyi sil
        if len(self._history) > self._max_points:
            self._history.pop(0)

        self._draw()                      # Grafiği güncelle

    def _draw(self):
        """Canvas üzerinde çizgi grafiği çiz."""
        self._canvas.delete("all")        # Önceki çizimi temizle

        w = self._canvas.winfo_width()    # Canvas genişliği (piksel)
        h = self._canvas.winfo_height()   # Canvas yüksekliği (piksel)

        if w <= 1 or len(self._history) < 2:
            return                        # Yeterli alan veya veri yoksa çizme

        # Her nokta arasındaki yatay mesafe
        step = w / (self._max_points - 1) if self._max_points > 1 else w

        points = []
        for i, val in enumerate(self._history):
            x = i * step                  # Yatay konum
            # Dikey konum: yüksek değer → yukarı (ters çevir)
            y = h - (val / self._max_val) * (h - 8) - 4
            y = max(4, min(h - 4, y))    # Canvas sınırları içinde tut
            points.extend([x, y])         # [x1,y1,x2,y2,...] formatı

        # Yeterli nokta varsa çizgi çiz
        if len(points) >= 4:
            self._canvas.create_line(
                *points,
                fill=self._color,
                width=2,
                smooth=True               # Pürüzsüz eğri
            )

            # Son noktaya belirteç (vurgu noktası) ekle
            lx, ly = points[-2], points[-1]
            self._canvas.create_oval(
                lx - 3, ly - 3,
                lx + 3, ly + 3,
                fill=self._color,
                outline=""                # Çerçevesiz
            )


# =============================================================================
# UYARI PANELI BİLEŞENİ
# =============================================================================
class AlertPanel:
    """Anlık uyarıları gösteren panel bileşeni."""

    def __init__(self, parent):
        frame = tk.Frame(parent, bg=ColorPalette.BG_CARD, bd=0)
        frame.pack(fill="both", expand=True, padx=6, pady=4)

        tk.Label(
            frame,
            text="CANLI UYARILAR",
            font=("Courier New", 7, "bold"),
            fg=ColorPalette.TEXT_SECONDARY,
            bg=ColorPalette.BG_CARD
        ).pack(anchor="w", padx=10, pady=(8, 4))

        # Kaydırılabilir metin alanı
        self._text = tk.Text(
            frame,
            height=6,                     # 6 satır yükseklik
            bg="#0D1117",
            fg=ColorPalette.ACCENT_GREEN,
            font=("Courier New", 8),
            state="disabled",             # Kullanıcı düzenleyemesin
            relief="flat",
            bd=0,
            insertbackground=ColorPalette.ACCENT_CYAN
        )
        self._text.pack(fill="both", expand=True, padx=10, pady=(0, 8))

    def update_alerts(self, alerts: list):
        """Uyarı listesini güncelle."""
        self._text.config(state="normal")    # Düzenlemeye izin ver
        self._text.delete("1.0", "end")      # Önceki içeriği sil

        if not alerts:
            self._text.insert("end", "  ✓  Sistem normal – aktif uyarı yok\n",
                               "ok")
            self._text.tag_config("ok", foreground=ColorPalette.ACCENT_GREEN)
        else:
            for alert in alerts:
                level = alert.get("level", "")
                msg = alert.get("msg", "")
                ts = alert.get("timestamp", "")
                color = ColorPalette.ACCENT_RED if level == "KRİTİK" else ColorPalette.ACCENT_YELLOW
                tag = f"tag_{id(alert)}"  # Her uyarı için benzersiz etiket
                line = f"  [{ts}] {level}: {msg}\n"
                self._text.insert("end", line, tag)
                self._text.tag_config(tag, foreground=color)

        self._text.config(state="disabled")  # Tekrar kilitle


# =============================================================================
# ANA UYGULAMA SINIFI
# Tüm bileşenleri bir araya getirir ve arka plan döngüsünü yönetir
# =============================================================================
class GameMonitorApp:
    """Ana uygulama sınıfı – arayüzü, sensörleri ve analizi yönetir."""

    def __init__(self, root: tk.Tk):
        self._root = root                 # Tkinter ana pencere
        self._running = False             # İzleme döngüsü çalışıyor mu?
        self._thread = None               # Arka plan iş parçacığı

        # Temel nesneleri başlat
        self._sensors = SensorGroup()             # Tüm sensörler
        self._profile_mgr = GameProfileManager()  # Profil yöneticisi
        self._evaluator = SystemEvaluator()        # Değerlendirici
        self._alert_mgr = AlertManager()           # Uyarı yöneticisi
        self._reporter = ReportGenerator()         # Rapor üreticisi

        self._current_profile = "orta"            # Aktif oyun profili
        self._reading_count = 0                   # Toplam okuma sayacı

        self._setup_window()                       # Pencere ayarları
        self._build_ui()                           # Arayüzü oluştur
        self._apply_profile(self._current_profile) # Profili uygula

    # ---------- Pencere Ayarları ----------

    def _setup_window(self):
        """Ana pencere özelliklerini ayarla."""
        self._root.title("⚡ GameSpy Monitor — Kastamonu Ü. Tosya MYO")
        self._root.configure(bg=ColorPalette.BG_DARK)
        self._root.geometry("1100x740")           # Başlangıç boyutu
        self._root.minsize(900, 620)              # Minimum boyut

        # Pencereyi ekranın ortasına yerleştir
        self._root.update_idletasks()
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        x = (sw - 1100) // 2
        y = (sh - 740) // 2
        self._root.geometry(f"1100x740+{x}+{y}")

        # Kapatma olayını yakala (onay sor)
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------- Arayüz Oluşturma ----------

    def _build_ui(self):
        """Tüm UI bileşenlerini oluştur."""
        self._build_header()              # Üst başlık çubuğu
        self._build_toolbar()             # Araç çubuğu (butonlar)
        self._build_content()             # Ana içerik alanı
        self._build_status_bar()          # Alt durum çubuğu

    def _build_header(self):
        """Başlık bölümünü oluştur."""
        header = tk.Frame(self._root, bg=ColorPalette.BG_HEADER, height=55)
        header.pack(fill="x")
        header.pack_propagate(False)      # Sabit yüksekliği koru

        # Uygulama logosu/adı
        tk.Label(
            header,
            text="⚡  GAMESPY MONITOR",
            font=("Courier New", 16, "bold"),
            fg=ColorPalette.ACCENT_CYAN,
            bg=ColorPalette.BG_HEADER
        ).pack(side="left", padx=20, pady=10)

        # Alt başlık
        tk.Label(
            header,
            text="Sistem Performans İzleme Aracı  |  Kastamonu Ü. Tosya MYO",
            font=("Courier New", 8),
            fg=ColorPalette.TEXT_SECONDARY,
            bg=ColorPalette.BG_HEADER
        ).pack(side="left", pady=10)

        # Saat göstergesi (sağ taraf)
        self._clock_label = tk.Label(
            header,
            text="",
            font=("Courier New", 10, "bold"),
            fg=ColorPalette.TEXT_DIM,
            bg=ColorPalette.BG_HEADER
        )
        self._clock_label.pack(side="right", padx=20)
        self._update_clock()              # Saati başlat

    def _build_toolbar(self):
        """Araç çubuğunu oluştur."""
        toolbar = tk.Frame(self._root, bg=ColorPalette.BG_PANEL, height=48)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        # Profil seçici etiketi
        tk.Label(
            toolbar,
            text="OyUN PROFİLİ:",
            font=("Courier New", 8, "bold"),
            fg=ColorPalette.TEXT_SECONDARY,
            bg=ColorPalette.BG_PANEL
        ).pack(side="left", padx=(15, 5), pady=14)

        # Profil butonları
        profiles = GameProfileManager.list_profiles()
        self._profile_buttons = {}
        for profile in profiles:
            info = GameProfileManager.PROFILES[profile]
            btn = tk.Button(
                toolbar,
                text=info["label"],
                font=("Courier New", 8, "bold"),
                bg=ColorPalette.BG_CARD,
                fg=ColorPalette.TEXT_PRIMARY,
                relief="flat",
                bd=0,
                padx=10,
                pady=4,
                cursor="hand2",           # El imleci
                command=lambda p=profile: self._apply_profile(p)
            )
            btn.pack(side="left", padx=3, pady=10)
            self._profile_buttons[profile] = btn

        # Ayırıcı çizgi
        tk.Frame(toolbar, bg=ColorPalette.TEXT_DIM, width=1).pack(
            side="left", fill="y", padx=15, pady=8
        )

        # Başlat/Durdur butonu
        self._toggle_btn = tk.Button(
            toolbar,
            text="▶  BAŞLAT",
            font=("Courier New", 9, "bold"),
            bg=ColorPalette.ACCENT_GREEN,
            fg="#000000",                 # Siyah metin (kontrast için)
            relief="flat",
            bd=0,
            padx=15,
            pady=4,
            cursor="hand2",
            command=self._toggle_monitoring
        )
        self._toggle_btn.pack(side="left", padx=5, pady=10)

        # Rapor butonu
        self._report_btn = tk.Button(
            toolbar,
            text="📋  RAPOR",
            font=("Courier New", 9, "bold"),
            bg=ColorPalette.ACCENT_PURPLE,
            fg=ColorPalette.TEXT_PRIMARY,
            relief="flat",
            bd=0,
            padx=15,
            pady=4,
            cursor="hand2",
            command=self._show_report
        )
        self._report_btn.pack(side="left", padx=5, pady=10)

        # Sıfırla butonu
        tk.Button(
            toolbar,
            text="↺  SIFIRLA",
            font=("Courier New", 9, "bold"),
            bg=ColorPalette.BG_CARD,
            fg=ColorPalette.TEXT_SECONDARY,
            relief="flat",
            bd=0,
            padx=15,
            pady=4,
            cursor="hand2",
            command=self._reset_session
        ).pack(side="left", padx=5, pady=10)

    def _build_content(self):
        """Ana içerik alanını oluştur."""
        content = tk.Frame(self._root, bg=ColorPalette.BG_DARK)
        content.pack(fill="both", expand=True, padx=5, pady=5)

        # Sol panel (metrik kartları)
        left = tk.Frame(content, bg=ColorPalette.BG_DARK)
        left.pack(side="left", fill="both", expand=True)

        # Sağ panel (grafikler + uyarılar)
        right = tk.Frame(content, bg=ColorPalette.BG_DARK, width=280)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        self._build_metric_grid(left)     # Sol: metrik kartlar
        self._build_charts_panel(right)   # Sağ: grafikler
        self._build_alerts_panel(right)   # Sağ alt: uyarılar

    def _build_metric_grid(self, parent):
        """Metrik kart ızgarasını oluştur."""
        # Izgara sütunlarını eşit genişlikte yapılandır
        grid = tk.Frame(parent, bg=ColorPalette.BG_DARK)
        grid.pack(fill="both", expand=True)

        for col in range(4):              # 4 sütunlu ızgara
            grid.columnconfigure(col, weight=1)
        for row in range(3):              # 3 satır
            grid.rowconfigure(row, weight=1)

        # Metrik kartları oluştur ve sözlükte sakla
        self._cards = {}

        # Satır 0: FPS, CPU Sıcaklık, GPU Sıcaklık, Sistem Puanı
        self._cards["fps"] = MetricCard(grid, "FPS", "kare/sn", 0, 0)
        self._cards["cpu_temp"] = MetricCard(grid, "CPU Sıcaklık", "°C", 1, 0)
        self._cards["gpu_temp"] = MetricCard(grid, "GPU Sıcaklık", "°C", 2, 0)
        self._cards["score"] = MetricCard(grid, "Sistem Puanı", "/ 100", 3, 0)

        # Satır 1: CPU Kullanım, RAM Kullanım, Disk, Ağ
        self._cards["cpu_usage"] = MetricCard(grid, "CPU Kullanım", "%", 0, 1)
        self._cards["ram_usage"] = MetricCard(grid, "RAM Kullanım", "%", 1, 1)
        self._cards["disk"] = MetricCard(grid, "Disk Doluluk", "%", 2, 1)
        self._cards["network"] = MetricCard(grid, "Ağ Hızı", "Mbps", 3, 1)

        # Satır 2: Pil, Disk I/O, RAM GB, Süre
        self._cards["battery"] = MetricCard(grid, "Pil Durumu", "%", 0, 2)
        self._cards["disk_io"] = MetricCard(grid, "Disk I/O", "MB/s", 1, 2)
        self._cards["ram_gb"] = MetricCard(grid, "RAM Kullanım", "GB", 2, 2)
        self._cards["uptime"] = MetricCard(grid, "İzleme Süresi", "dk:sn", 3, 2)

        self._start_time = None           # Başlangıç zamanı (süre için)

    def _build_charts_panel(self, parent):
        """Grafik panelini oluştur."""
        panel = tk.Frame(parent, bg=ColorPalette.BG_DARK)
        panel.pack(fill="x", padx=0, pady=0)

        tk.Label(
            panel,
            text="CANLI GRAFİKLER",
            font=("Courier New", 7, "bold"),
            fg=ColorPalette.TEXT_DIM,
            bg=ColorPalette.BG_DARK
        ).pack(anchor="w", padx=16, pady=(8, 2))

        # FPS, CPU ve GPU için mini grafikler
        self._chart_fps = MiniChart(panel, "FPS", ColorPalette.ACCENT_CYAN, 200)
        self._chart_cpu = MiniChart(panel, "CPU Sıcaklık (°C)", ColorPalette.ACCENT_ORANGE, 100)
        self._chart_gpu = MiniChart(panel, "GPU Sıcaklık (°C)", ColorPalette.ACCENT_PURPLE, 100)

    def _build_alerts_panel(self, parent):
        """Uyarı panelini oluştur."""
        self._alert_panel = AlertPanel(parent)

    def _build_status_bar(self):
        """Alt durum çubuğunu oluştur."""
        bar = tk.Frame(self._root, bg=ColorPalette.BG_HEADER, height=26)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self._status_label = tk.Label(
            bar,
            text="  Hazır – Başlatmak için ▶ BAŞLAT tuşuna basın",
            font=("Courier New", 8),
            fg=ColorPalette.TEXT_DIM,
            bg=ColorPalette.BG_HEADER,
            anchor="w"
        )
        self._status_label.pack(side="left", padx=10, fill="x")

        # Sağda okuma sayacı
        self._reading_label = tk.Label(
            bar,
            text="Ölçüm: 0",
            font=("Courier New", 8),
            fg=ColorPalette.TEXT_DIM,
            bg=ColorPalette.BG_HEADER
        )
        self._reading_label.pack(side="right", padx=10)

    # ---------- Yardımcı Metotlar ----------

    def _update_clock(self):
        """Saati her saniye güncelle."""
        now = datetime.now().strftime("%d.%m.%Y  %H:%M:%S")
        self._clock_label.config(text=now)
        self._root.after(1000, self._update_clock)  # 1 saniye sonra tekrar çağır

    def _apply_profile(self, profile_name: str):
        """Seçilen oyun profilini uygula ve buton görünümünü güncelle."""
        self._current_profile = profile_name
        self._profile_mgr.apply_profile(profile_name, self._sensors)

        # Profil butonlarını görsel olarak güncelle
        for name, btn in self._profile_buttons.items():
            if name == profile_name:
                btn.config(
                    bg=ColorPalette.ACCENT_CYAN,
                    fg="#000000"           # Aktif buton siyah metin
                )
            else:
                btn.config(
                    bg=ColorPalette.BG_CARD,
                    fg=ColorPalette.TEXT_PRIMARY
                )

        # Değerlendiriciyi güncelle
        target = GameProfileManager.PROFILES[profile_name]["fps_target"]
        self._evaluator = SystemEvaluator(target_fps=target)

        # Durum çubuğunu güncelle
        label = GameProfileManager.PROFILES[profile_name]["label"]
        self._status_label.config(text=f"  Profil: {label}")

    def _get_value_color(self, metric: str, value: float) -> str:
        """Metrik değerine göre uygun rengi döndür."""
        color_map = {
            "fps": [
                (60, ColorPalette.STATUS_GOOD),
                (30, ColorPalette.STATUS_WARN),
                (0, ColorPalette.STATUS_CRIT)
            ],
            "cpu_temp": [
                (65, ColorPalette.STATUS_GOOD),
                (80, ColorPalette.STATUS_WARN),
                (100, ColorPalette.STATUS_CRIT)
            ],
            "gpu_temp": [
                (70, ColorPalette.STATUS_GOOD),
                (83, ColorPalette.STATUS_WARN),
                (100, ColorPalette.STATUS_CRIT)
            ],
            "usage": [                   # CPU ve RAM için ortak
                (60, ColorPalette.STATUS_GOOD),
                (85, ColorPalette.STATUS_WARN),
                (100, ColorPalette.STATUS_CRIT)
            ]
        }
        thresholds = color_map.get(metric, color_map["usage"])

        if metric == "fps":
            # FPS için: yüksek değer iyi (ters mantık)
            if value >= thresholds[0][0]: return thresholds[0][1]
            if value >= thresholds[1][0]: return thresholds[1][1]
            return thresholds[2][1]
        else:
            # Sıcaklık/kullanım: düşük değer iyi
            if value <= thresholds[0][0]: return thresholds[0][1]
            if value <= thresholds[1][0]: return thresholds[1][1]
            return thresholds[2][1]

    # ---------- İzleme Döngüsü ----------

    def _toggle_monitoring(self):
        """İzlemeyi başlat veya durdur."""
        if self._running:
            self._stop_monitoring()
        else:
            self._start_monitoring()

    def _start_monitoring(self):
        """İzlemeyi başlat."""
        self._running = True
        self._start_time = time.time()   # Başlangıç zamanını kaydet
        self._toggle_btn.config(
            text="■  DURDUR",
            bg=ColorPalette.ACCENT_RED
        )
        self._status_label.config(
            text=f"  İzleme aktif – Profil: {GameProfileManager.PROFILES[self._current_profile]['label']}"
        )
        # Arka plan iş parçacığı oluştur ve başlat
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def _stop_monitoring(self):
        """İzlemeyi durdur."""
        self._running = False
        self._toggle_btn.config(
            text="▶  BAŞLAT",
            bg=ColorPalette.ACCENT_GREEN
        )
        self._status_label.config(text="  İzleme durduruldu")

    def _monitor_loop(self):
        """Arka planda çalışan veri toplama döngüsü."""
        while self._running:
            try:
                data = self._sensors.read_all()              # Tüm sensörleri oku
                result = self._evaluator.evaluate_snapshot(data)  # Değerlendir
                alerts = self._alert_mgr.check(data)         # Uyarıları kontrol et
                self._reading_count += 1                     # Sayacı artır

                # GUI güncellemesi için ana iş parçacığını kullan
                self._root.after(0, self._update_ui, data, result, alerts)

            except Exception as e:
                print(f"İzleme hatası: {e}")                 # Hataları konsola yaz

            time.sleep(1.5)              # 1.5 saniyede bir güncelle

    def _update_ui(self, data: dict, result: dict, alerts: list):
        """GUI bileşenlerini güncel verilerle güncelle (ana iş parçacığında)."""
        scores = result.get("scores", {})

        # FPS kartı
        fps = data.get("fps", 0)
        self._cards["fps"].update(
            fps,
            f"Kararlılık: {data.get('fps_stability', 0):.0f}%",
            self._get_value_color("fps", fps)
        )

        # CPU sıcaklık kartı
        ct = data.get("cpu_temp", 0)
        self._cards["cpu_temp"].update(
            ct,
            data.get("cpu_status", ""),
            self._get_value_color("cpu_temp", ct)
        )

        # GPU sıcaklık kartı
        gt = data.get("gpu_temp", 0)
        self._cards["gpu_temp"].update(
            gt,
            data.get("gpu_status", ""),
            self._get_value_color("gpu_temp", gt)
        )

        # Sistem puanı kartı
        total = scores.get("total", 0)
        self._cards["score"].update(
            total,
            result.get("overall_grade", ""),
            self._get_value_color("fps", total)  # Yüksek puan = iyi
        )

        # CPU kullanım kartı
        cu = data.get("cpu_usage", 0)
        self._cards["cpu_usage"].update(
            cu, "", self._get_value_color("usage", cu)
        )

        # RAM kullanım kartı
        ru = data.get("ram_usage", 0)
        self._cards["ram_usage"].update(
            ru, "", self._get_value_color("usage", ru)
        )

        # Disk doluluk kartı
        du = data.get("disk_usage", 0)
        self._cards["disk"].update(
            du, "", self._get_value_color("usage", du)
        )

        # Ağ hızı kartı
        ns = data.get("network_speed", 0)
        self._cards["network"].update(
            ns, "Mbps", ColorPalette.ACCENT_CYAN
        )

        # Pil durumu kartı
        bat = data.get("battery", 100)
        bat_text = "Şarj oluyor" if data.get("battery_charging") else "Pil"
        self._cards["battery"].update(bat, bat_text, ColorPalette.ACCENT_GREEN)

        # Disk I/O kartı
        self._cards["disk_io"].update(
            data.get("disk_io", 0), "", ColorPalette.ACCENT_ORANGE
        )

        # RAM GB kartı
        used_gb = data.get("ram_used_gb", 0)
        total_gb = data.get("ram_total_gb", 16)
        self._cards["ram_gb"].update(
            used_gb, f"/ {total_gb} GB", ColorPalette.ACCENT_PURPLE
        )

        # İzleme süresi kartı
        if self._start_time:
            elapsed = int(time.time() - self._start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            self._cards["uptime"].update(
                f"{minutes:02d}:{seconds:02d}", "", ColorPalette.TEXT_SECONDARY
            )

        # Grafikleri güncelle
        self._chart_fps.add_value(fps)
        self._chart_cpu.add_value(ct)
        self._chart_gpu.add_value(gt)

        # Uyarı panelini güncelle
        self._alert_panel.update_alerts(alerts)

        # Alt çubuğu güncelle
        self._reading_label.config(text=f"Ölçüm: {self._reading_count}")

    # ---------- Oturum İşlemleri ----------

    def _reset_session(self):
        """Oturumu sıfırla."""
        if self._running:
            messagebox.showwarning("Uyarı", "Önce izlemeyi durdurun!")
            return
        self._sensors.reset_all()                        # Sensör geçmişini sıfırla
        self._evaluator = SystemEvaluator(
            GameProfileManager.PROFILES[self._current_profile]["fps_target"]
        )
        self._alert_mgr = AlertManager()                 # Uyarıları sıfırla
        self._reading_count = 0                          # Sayacı sıfırla
        self._start_time = None

        # Kartları sıfırla
        for card in self._cards.values():
            card.update("---", "", ColorPalette.ACCENT_CYAN)

        self._status_label.config(text="  Oturum sıfırlandı")

    def _show_report(self):
        """Oturum raporunu bir diyalog penceresinde göster."""
        stats = self._evaluator.get_session_stats()
        if not stats:
            messagebox.showinfo("Bilgi", "Henüz yeterli veri toplanmadı.")
            return

        alert_counts = self._alert_mgr.get_alert_count()
        report_text = self._reporter.generate_text_report(stats, alert_counts)

        # Yeni pencere oluştur
        win = tk.Toplevel(self._root)
        win.title("Oturum Raporu")
        win.configure(bg=ColorPalette.BG_DARK)
        win.geometry("520x440")

        text_widget = tk.Text(
            win,
            bg="#0D1117",
            fg=ColorPalette.ACCENT_CYAN,
            font=("Courier New", 9),
            relief="flat",
            bd=0,
            padx=15,
            pady=15
        )
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        text_widget.insert("1.0", report_text)
        text_widget.config(state="disabled")

        # JSON kaydet butonu
        tk.Button(
            win,
            text="JSON Olarak Kaydet",
            font=("Courier New", 9, "bold"),
            bg=ColorPalette.ACCENT_PURPLE,
            fg=ColorPalette.TEXT_PRIMARY,
            relief="flat",
            bd=0,
            padx=15, pady=6,
            cursor="hand2",
            command=lambda: self._save_report(stats)
        ).pack(pady=(0, 10))

    def _save_report(self, stats: dict):
        """Raporu JSON dosyasına kaydet."""
        success = self._reporter.save_json_report(stats)
        if success:
            messagebox.showinfo("Başarılı", "Rapor 'session_report.json' olarak kaydedildi.")
        else:
            messagebox.showerror("Hata", "Dosya kaydedilemedi.")

    def _on_close(self):
        """Pencere kapatılırken onay sor."""
        if self._running:
            if messagebox.askyesno("Çıkış", "İzleme aktif. Yine de çıkmak istiyor musunuz?"):
                self._running = False
                self._root.destroy()
        else:
            self._root.destroy()


# =============================================================================
# PROGRAM GİRİŞ NOKTASI
# =============================================================================
def main():
    """Uygulamayı başlat."""
    root = tk.Tk()                        # Ana Tkinter penceresi oluştur
    app = GameMonitorApp(root)            # Uygulama nesnesini oluştur
    root.mainloop()                       # GUI döngüsünü başlat (kapatılana kadar çalış)


if __name__ == "__main__":
    main()                                # Sadece doğrudan çalıştırılırsa main() çağır
