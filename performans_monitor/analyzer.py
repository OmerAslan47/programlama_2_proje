# =============================================================================
# analyzer.py - Sistem Değerlendirme Modülü
# Kastamonu Üniversitesi Tosya MYO - Programlama II Dönem Projesi
# Bu modül; toplanan verileri analiz eder, puan verir ve rapor üretir.
# =============================================================================

from datetime import datetime   # Tarih/saat işlemleri için
import json                     # JSON dosyasına kaydetmek için


# =============================================================================
# TEMEL ANALİZ SINIFI: AnalyzerBase
# Tüm analizörler bu sınıftan kalıtım alır
# =============================================================================
class AnalyzerBase:
    """Tüm analizör sınıfları için temel sınıf."""

    def __init__(self, analyzer_name: str):
        self._name = analyzer_name        # Analizör adı (kapsülleme)
        self._threshold_good = 0          # "İyi" eşik değeri (alt sınıf ayarlar)
        self._threshold_warn = 0          # "Uyarı" eşik değeri
        self._threshold_bad = 0           # "Kötü" eşik değeri

    @property
    def name(self):
        """Analizör adını döndür."""
        return self._name

    def analyze(self, value: float) -> str:
        """Değeri analiz et – alt sınıflar override eder."""
        raise NotImplementedError("analyze() metodu alt sınıfta tanımlanmalıdır!")

    def score(self, value: float) -> float:
        """0-100 arası puan döndür – alt sınıflar override eder."""
        raise NotImplementedError("score() metodu alt sınıfta tanımlanmalıdır!")

    @staticmethod
    def _clamp(value: float, min_val: float, max_val: float) -> float:
        """Değeri belirtilen aralığa sıkıştır (yardımcı metot)."""
        return max(min_val, min(max_val, value))

    def __str__(self):
        return f"Analizör: {self._name}"


# =============================================================================
# FPS ANALİZÖRÜ - AnalyzerBase'den kalıtım alır
# =============================================================================
class FPSAnalyzer(AnalyzerBase):
    """FPS değerini analiz eden sınıf."""

    def __init__(self, target_fps: int = 60):
        super().__init__("FPS Analizörü")
        self._target_fps = target_fps     # Hedef FPS (başarı kriteri)

    def analyze(self, value: float) -> str:
        """FPS değerini kategorize et."""
        ratio = value / self._target_fps  # Hedef FPS'e oranla karşılaştır

        if ratio >= 0.95:                 # Hedefin %95'inden fazlası
            return "mükemmel"
        elif ratio >= 0.75:               # Hedefin %75-95 arası
            return "iyi"
        elif ratio >= 0.50:               # Hedefin %50-75 arası
            return "orta"
        elif ratio >= 0.30:               # Hedefin %30-50 arası
            return "düşük"
        else:                             # %30'dan az
            return "kritik"

    def score(self, value: float) -> float:
        """FPS için 0-100 puan hesapla."""
        if value <= 0:
            return 0.0
        ratio = value / self._target_fps
        raw_score = min(100.0, ratio * 100)  # Oransal puan
        return round(raw_score, 1)

    def check_stutter(self, fps_list: list) -> bool:
        """FPS listesinde titreme (stutter) var mı kontrol et."""
        if len(fps_list) < 3:
            return False
        for i in range(1, len(fps_list)):
            drop = fps_list[i - 1] - fps_list[i]  # Ardışık fark
            if drop > 20:                 # 20 FPS'den fazla ani düşüş = stutter
                return True
        return False


# =============================================================================
# SICAKLIK ANALİZÖRÜ - AnalyzerBase'den kalıtım alır
# =============================================================================
class TemperatureAnalyzer(AnalyzerBase):
    """Sıcaklık değerlerini analiz eden sınıf."""

    def __init__(self, component: str = "CPU"):
        super().__init__(f"{component} Sıcaklık Analizörü")
        self._component = component       # "CPU" veya "GPU"
        # Bileşene göre eşik değerlerini ayarla
        if component == "GPU":
            self._threshold_good = 70     # GPU için iyi eşiği
            self._threshold_warn = 83     # GPU için uyarı eşiği
            self._threshold_bad = 92      # GPU için tehlike eşiği
        else:                             # CPU ve diğerleri
            self._threshold_good = 65
            self._threshold_warn = 80
            self._threshold_bad = 95

    def analyze(self, value: float) -> str:
        """Sıcaklık değerini kategorize et."""
        if value < self._threshold_good:
            return "soğuk/normal"
        elif value < self._threshold_warn:
            return "ılık"
        elif value < self._threshold_bad:
            return "sıcak (uyarı)"
        else:
            return "aşırı sıcak (kritik)"

    def score(self, value: float) -> float:
        """Düşük sıcaklık = yüksek puan mantığıyla 0-100 puan hesapla."""
        if value <= self._threshold_good:
            # İyi eşiğin altındaysa tam puan
            score = 100.0
        elif value >= self._threshold_bad:
            # Tehlike eşiğinde veya üstündeyse sıfır puan
            score = 0.0
        else:
            # Lineer interpolasyon: uyarı bölgesi
            range_size = self._threshold_bad - self._threshold_good
            excess = value - self._threshold_good
            score = 100.0 * (1 - excess / range_size)

        return round(self._clamp(score, 0.0, 100.0), 1)


# =============================================================================
# KAYNAK KULLANIM ANALİZÖRÜ - AnalyzerBase'den kalıtım alır
# CPU/RAM/Disk yüzde değerleri için ortak analiz
# =============================================================================
class UsageAnalyzer(AnalyzerBase):
    """Yüzde kullanım değerleri için genel analizör (CPU, RAM, Disk)."""

    def __init__(self, resource_name: str, invert_score: bool = True):
        super().__init__(f"{resource_name} Kullanım Analizörü")
        self._resource = resource_name
        self._invert_score = invert_score  # True: düşük kullanım = yüksek puan

    def analyze(self, value: float) -> str:
        """Kullanım yüzdesini kategorize et."""
        if value < 40:
            return "düşük (iyi)"
        elif value < 65:
            return "orta"
        elif value < 85:
            return "yüksek"
        else:
            return "çok yüksek (kritik)"

    def score(self, value: float) -> float:
        """Kullanım yüzdesi için puan hesapla."""
        if self._invert_score:
            # Düşük kullanım = iyi performans
            raw_score = 100.0 - value     # %80 kullanım → 20 puan
        else:
            raw_score = value             # Kullanım yüksek olursa iyi (nadir durum)

        return round(self._clamp(raw_score, 0.0, 100.0), 1)


# =============================================================================
# GENEL SİSTEM DEĞERLENDİRİCİSİ
# Tüm analizörleri bir araya getirir ve genel sistem puanı üretir
# =============================================================================
class SystemEvaluator:
    """Tüm metrikleri değerlendiren ve genel puan veren ana sınıf."""

    # Ağırlık tablosu: Her metriğin genel puana katkısı
    WEIGHTS = {
        "fps":        0.30,               # FPS oyun deneyimini en çok etkiler
        "cpu_temp":   0.15,               # CPU sıcaklığı donanım sağlığı açısından önemli
        "gpu_temp":   0.15,               # GPU sıcaklığı da kritik
        "cpu_usage":  0.15,               # CPU yükü genel performansı etkiler
        "ram_usage":  0.15,               # RAM doluluk performans darboğazı oluşturur
        "disk_usage": 0.05,               # Disk doluluk az kritik
        "network":    0.05,               # Ağ hızı oyun gecikme süresiyle ilişkili
    }

    def __init__(self, target_fps: int = 60):
        self._target_fps = target_fps     # Değerlendirme için hedef FPS
        # Her metrik için ayrı analizör nesnesi oluştur
        self._fps_analyzer = FPSAnalyzer(target_fps)
        self._cpu_temp_analyzer = TemperatureAnalyzer("CPU")
        self._gpu_temp_analyzer = TemperatureAnalyzer("GPU")
        self._cpu_usage_analyzer = UsageAnalyzer("CPU")
        self._ram_analyzer = UsageAnalyzer("RAM")
        self._disk_analyzer = UsageAnalyzer("Disk")
        self._network_analyzer = UsageAnalyzer("Ağ", invert_score=False)  # Yüksek hız iyi

        self._session_scores = []         # Oturum boyunca hesaplanan puanlar
        self._session_data = []           # Oturum ham verileri (kayıt için)

    # ---------- Ortak Değerlendirme Metotları ----------

    def evaluate_snapshot(self, data: dict) -> dict:
        """Tek bir anlık ölçüm verisini değerlendir."""

        # Her metrik için ayrı puan hesapla
        fps_score = self._fps_analyzer.score(data.get("fps", 0))
        cpu_temp_score = self._cpu_temp_analyzer.score(data.get("cpu_temp", 50))
        gpu_temp_score = self._gpu_temp_analyzer.score(data.get("gpu_temp", 50))
        cpu_usage_score = self._cpu_usage_analyzer.score(data.get("cpu_usage", 50))
        ram_score = self._ram_analyzer.score(data.get("ram_usage", 50))
        disk_score = self._disk_analyzer.score(data.get("disk_usage", 50))

        # Ağ: 25 Mbps'yi tam puan kabul et, oransal hesap yap
        raw_net = min(data.get("network_speed", 0) / 25 * 100, 100)
        network_score = round(raw_net, 1)

        # Ağırlıklı toplam puan hesapla
        W = self.WEIGHTS
        total_score = (
            fps_score * W["fps"] +
            cpu_temp_score * W["cpu_temp"] +
            gpu_temp_score * W["gpu_temp"] +
            cpu_usage_score * W["cpu_usage"] +
            ram_score * W["ram_usage"] +
            disk_score * W["disk_usage"] +
            network_score * W["network"]
        )
        total_score = round(total_score, 1)

        # Sonuç sözlüğü hazırla
        result = {
            "timestamp": data.get("timestamp", ""),
            "scores": {
                "fps": fps_score,
                "cpu_temp": cpu_temp_score,
                "gpu_temp": gpu_temp_score,
                "cpu_usage": cpu_usage_score,
                "ram": ram_score,
                "disk": disk_score,
                "network": network_score,
                "total": total_score
            },
            "ratings": {
                "fps": self._fps_analyzer.analyze(data.get("fps", 0)),
                "cpu_temp": self._cpu_temp_analyzer.analyze(data.get("cpu_temp", 50)),
                "gpu_temp": self._gpu_temp_analyzer.analyze(data.get("gpu_temp", 50)),
                "cpu_usage": self._cpu_usage_analyzer.analyze(data.get("cpu_usage", 50)),
                "ram": self._ram_analyzer.analyze(data.get("ram_usage", 50))
            },
            "overall_grade": self._grade(total_score)  # Harf notu
        }

        self._session_scores.append(total_score)  # Oturum listesine ekle
        self._session_data.append(data)           # Ham veriyi kaydet
        return result

    def _grade(self, score: float) -> str:
        """Puana göre harf notu ver."""
        if score >= 85:
            return "A - Mükemmel"
        elif score >= 70:
            return "B - İyi"
        elif score >= 55:
            return "C - Orta"
        elif score >= 40:
            return "D - Zayıf"
        else:
            return "F - Kritik"

    def get_session_average(self) -> float:
        """Oturum boyunca hesaplanan toplam puanların ortalaması."""
        if not self._session_scores:
            return 0.0
        return round(sum(self._session_scores) / len(self._session_scores), 1)

    def get_session_stats(self) -> dict:
        """Oturum istatistiklerini döndür."""
        if not self._session_data:
            return {}

        # Ham verilerden her metrik için ortalama hesapla
        def avg(key):
            vals = [d.get(key, 0) for d in self._session_data]
            return round(sum(vals) / len(vals), 1) if vals else 0.0

        return {
            "total_readings": len(self._session_data),     # Toplam ölçüm sayısı
            "avg_fps": avg("fps"),                         # Ortalama FPS
            "avg_cpu_temp": avg("cpu_temp"),               # Ortalama CPU sıcaklığı
            "avg_gpu_temp": avg("gpu_temp"),               # Ortalama GPU sıcaklığı
            "avg_cpu_usage": avg("cpu_usage"),             # Ortalama CPU kullanımı
            "avg_ram_usage": avg("ram_usage"),             # Ortalama RAM kullanımı
            "avg_network": avg("network_speed"),           # Ortalama ağ hızı
            "avg_system_score": self.get_session_average(), # Ortalama sistem puanı
            "overall_grade": self._grade(self.get_session_average())
        }


# =============================================================================
# UYARI YÖNETİCİSİ - AnalyzerBase'den kalıtım alır
# =============================================================================
class AlertManager(AnalyzerBase):
    """Eşik değeri aşıldığında uyarı üreten yönetici sınıf."""

    def __init__(self):
        super().__init__("Uyarı Yöneticisi")
        self._active_alerts = []          # Aktif uyarılar listesi
        self._alert_history = []          # Tüm geçmiş uyarılar

        # Uyarı eşikleri sözlüğü
        self._thresholds = {
            "cpu_temp_warn": 80,          # CPU uyarı sıcaklığı
            "cpu_temp_crit": 92,          # CPU kritik sıcaklığı
            "gpu_temp_warn": 83,          # GPU uyarı sıcaklığı
            "gpu_temp_crit": 90,          # GPU kritik sıcaklığı
            "cpu_usage_warn": 85,         # CPU kullanım uyarısı
            "ram_usage_warn": 85,         # RAM kullanım uyarısı
            "disk_usage_warn": 90,        # Disk doluluk uyarısı
            "fps_low": 20,                # Düşük FPS uyarısı
        }

    def analyze(self, value: float) -> str:
        """AnalyzerBase sözleşmesini yerine getir."""
        return "uyarı" if value > 0 else "normal"

    def score(self, value: float) -> float:
        """Aktif uyarı sayısına göre skor (az uyarı = yüksek puan)."""
        alert_count = len(self._active_alerts)
        return max(0.0, 100.0 - alert_count * 20)  # Her uyarı 20 puan düşürür

    def check(self, data: dict) -> list:
        """Veri setini kontrol et ve uyarıları güncelle."""
        new_alerts = []
        T = self._thresholds             # Kısaltma: eşik değerleri

        # CPU sıcaklık kontrol
        cpu_t = data.get("cpu_temp", 0)
        if cpu_t >= T["cpu_temp_crit"]:
            new_alerts.append({"level": "KRİTİK", "msg": f"CPU sıcaklığı {cpu_t}°C (eşik: {T['cpu_temp_crit']}°C)"})
        elif cpu_t >= T["cpu_temp_warn"]:
            new_alerts.append({"level": "UYARI", "msg": f"CPU sıcaklığı {cpu_t}°C (eşik: {T['cpu_temp_warn']}°C)"})

        # GPU sıcaklık kontrol
        gpu_t = data.get("gpu_temp", 0)
        if gpu_t >= T["gpu_temp_crit"]:
            new_alerts.append({"level": "KRİTİK", "msg": f"GPU sıcaklığı {gpu_t}°C (eşik: {T['gpu_temp_crit']}°C)"})
        elif gpu_t >= T["gpu_temp_warn"]:
            new_alerts.append({"level": "UYARI", "msg": f"GPU sıcaklığı {gpu_t}°C (eşik: {T['gpu_temp_warn']}°C)"})

        # CPU kullanım kontrol
        cpu_u = data.get("cpu_usage", 0)
        if cpu_u >= T["cpu_usage_warn"]:
            new_alerts.append({"level": "UYARI", "msg": f"CPU kullanımı %{cpu_u} (eşik: %{T['cpu_usage_warn']})"})

        # RAM kullanım kontrol
        ram_u = data.get("ram_usage", 0)
        if ram_u >= T["ram_usage_warn"]:
            new_alerts.append({"level": "UYARI", "msg": f"RAM kullanımı %{ram_u} (eşik: %{T['ram_usage_warn']})"})

        # Disk doluluk kontrol
        disk_u = data.get("disk_usage", 0)
        if disk_u >= T["disk_usage_warn"]:
            new_alerts.append({"level": "UYARI", "msg": f"Disk doluluk %{disk_u} (eşik: %{T['disk_usage_warn']})"})

        # FPS kontrol
        fps = data.get("fps", 60)
        if fps <= T["fps_low"]:
            new_alerts.append({"level": "UYARI", "msg": f"FPS çok düşük: {fps} (eşik: {T['fps_low']})"})

        # Zaman damgası ekleyerek listeye kaydet
        ts = data.get("timestamp", datetime.now().strftime("%H:%M:%S"))
        for alert in new_alerts:
            alert["timestamp"] = ts
            self._alert_history.append(alert)  # Geçmişe ekle

        self._active_alerts = new_alerts      # Aktif uyarıları güncelle
        return new_alerts

    def get_active_alerts(self) -> list:
        """Geçerli aktif uyarıları döndür."""
        return list(self._active_alerts)

    def get_alert_count(self) -> dict:
        """Uyarı sayısını tür bazında döndür."""
        counts = {"KRİTİK": 0, "UYARI": 0}
        for a in self._alert_history:
            level = a.get("level", "UYARI")
            counts[level] = counts.get(level, 0) + 1
        return counts


# =============================================================================
# RAPOR ÜRETİCİ - AnalyzerBase'den kalıtım alır
# =============================================================================
class ReportGenerator(AnalyzerBase):
    """Oturum sonunda rapor üreten sınıf."""

    def __init__(self):
        super().__init__("Rapor Üreticisi")

    def analyze(self, value: float) -> str:
        """AnalyzerBase sözleşmesini yerine getir."""
        return "rapor_hazir"

    def score(self, value: float) -> float:
        """Raporlama skoru (her zaman tam)."""
        return 100.0

    def generate_text_report(self, stats: dict, alert_counts: dict) -> str:
        """Metin tabanlı oturum raporu oluştur."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Tarih saat formatı

        # Raporun başlık bölümü
        lines = [
            "=" * 60,
            "   OYUN PERFORMANS İZLEME RAPORU",
            f"   {now}",
            "=" * 60,
            "",
            "── ORTALAMA DEĞERLER ──────────────────────────",
            f"  FPS              : {stats.get('avg_fps', 0):.1f}",
            f"  CPU Sıcaklığı    : {stats.get('avg_cpu_temp', 0):.1f} °C",
            f"  GPU Sıcaklığı    : {stats.get('avg_gpu_temp', 0):.1f} °C",
            f"  CPU Kullanımı    : %{stats.get('avg_cpu_usage', 0):.1f}",
            f"  RAM Kullanımı    : %{stats.get('avg_ram_usage', 0):.1f}",
            f"  Ağ Hızı          : {stats.get('avg_network', 0):.1f} Mbps",
            "",
            "── SİSTEM PUANI ────────────────────────────────",
            f"  Genel Puan       : {stats.get('avg_system_score', 0):.1f} / 100",
            f"  Değerlendirme    : {stats.get('overall_grade', 'N/A')}",
            f"  Toplam Ölçüm     : {stats.get('total_readings', 0)} adet",
            "",
            "── UYARI ÖZETİ ─────────────────────────────────",
            f"  Kritik Uyarı     : {alert_counts.get('KRİTİK', 0)} adet",
            f"  Genel Uyarı      : {alert_counts.get('UYARI', 0)} adet",
            "",
            "=" * 60,
            "  Kastamonu Ü. Tosya MYO - Programlama II Projesi",
            "=" * 60,
        ]
        return "\n".join(lines)           # Satırları birleştir

    def save_json_report(self, stats: dict, filepath: str = "session_report.json"):
        """Raporu JSON dosyasına kaydet."""
        report = {
            "generated_at": datetime.now().isoformat(),   # ISO tarih formatı
            "session_stats": stats
        }
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)  # Güzel biçimlendirme
            return True
        except IOError as e:
            print(f"Dosya yazma hatası: {e}")
            return False
