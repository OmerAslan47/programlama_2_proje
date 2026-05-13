# monitor.py - Sistem verilerini toplayan sınıflar (OOP: Sınıf, Kalıtım, Kapsülleme)

import psutil          # CPU, RAM, disk bilgilerini okumak için
import time            # Zaman damgası ve bekleme işlemleri için
import random          # GPU simülasyonu için rastgele değer üretimi
from datetime import datetime  # Okunabilir tarih/saat formatı için


# ───────────────────────────────────────────────
# TEMEL SINIF (Base Class) - Tüm monitörlerin atası
# ───────────────────────────────────────────────
class BaseMonitor:
    """Tüm izleme sınıfları bu sınıftan türetilir (Kalıtım / Inheritance)."""

    def __init__(self, name: str):
        self._name = name          # Kapsülleme: alt çizgi ile "korumalı" alan
        self._history = []         # Ölçüm geçmişini tutan liste
        self._start_time = time.time()  # İzleme başlangıç zamanı

    # ── Kapsülleme: dışarıdan sadece okuma izni (property) ──
    @property
    def name(self):
        return self._name          # Monitör adını döndürür

    @property
    def history(self):
        return self._history       # Geçmiş verileri döndürür

    def collect(self) -> dict:
        """Alt sınıflar bu metodu override ederek veri toplar (Polimorfizm)."""
        raise NotImplementedError  # Doğrudan çağrılırsa hata fırlatır

    def _add_to_history(self, data: dict):
        """Toplanan veriyi geçmişe ekler; geçmiş en fazla 300 kayıt tutar."""
        data["timestamp"] = datetime.now().strftime("%H:%M:%S")  # Saat damgası
        self._history.append(data)      # Listeye ekle
        if len(self._history) > 300:    # Belleği aşırı doldurmamak için
            self._history.pop(0)        # En eski kaydı sil

    def get_average(self, key: str) -> float:
        """Belirtilen anahtarın geçmişteki ortalamasını hesaplar."""
        values = [r[key] for r in self._history if key in r]  # İlgili değerleri filtrele
        return round(sum(values) / len(values), 2) if values else 0.0  # Ortalama veya 0


# ───────────────────────────────────────────────
# CPU MONİTÖR SINIFI - BaseMonitor'dan türetildi
# ───────────────────────────────────────────────
class CPUMonitor(BaseMonitor):
    """CPU kullanımı, sıcaklık ve frekans bilgilerini toplar."""

    def __init__(self):
        super().__init__("CPU Monitor")   # Üst sınıfın __init__ metodunu çağır
        self._core_count = psutil.cpu_count(logical=True)  # Mantıksal çekirdek sayısı

    @property
    def core_count(self):
        return self._core_count           # Çekirdek sayısını dışarıya aç

    def _get_temperature(self) -> float:
        """CPU sıcaklığını okur; desteklenmiyorsa gerçekçi simülasyon üretir."""
        try:
            temps = psutil.sensors_temperatures()   # Donanım sensörlerini oku
            if temps:
                for key in ("coretemp", "cpu_thermal", "k10temp", "acpitz"):
                    if key in temps:                # Bilinen sensör adlarını dene
                        return round(temps[key][0].current, 1)  # İlk sensör değeri
        except (AttributeError, NotImplementedError):
            pass                                    # Desteklenmiyorsa geç
        # Simülasyon: kullanım oranına göre gerçekçi sıcaklık üret
        usage = psutil.cpu_percent(interval=None)
        return round(35 + (usage * 0.55) + random.uniform(-2, 2), 1)

    def collect(self) -> dict:
        """Anlık CPU verisini toplar ve geçmişe ekler."""
        usage = psutil.cpu_percent(interval=0.1)      # CPU kullanım yüzdesi
        freq  = psutil.cpu_freq()                     # CPU frekans bilgisi
        data  = {
            "usage"      : round(usage, 1),           # Kullanım (%)
            "temperature": self._get_temperature(),   # Sıcaklık (°C)
            "frequency"  : round(freq.current, 0) if freq else 0,  # Frekans (MHz)
            "cores"      : self._core_count,          # Çekirdek sayısı
        }
        self._add_to_history(data)   # Geçmişe kaydet
        return data                  # Veriyi döndür


# ───────────────────────────────────────────────
# GPU MONİTÖR SINIFI - BaseMonitor'dan türetildi
# ───────────────────────────────────────────────
class GPUMonitor(BaseMonitor):
    """GPU kullanımı ve sıcaklık bilgilerini toplar (simülasyon destekli)."""

    def __init__(self):
        super().__init__("GPU Monitor")   # Üst sınıfı başlat
        self._gpu_available = self._check_gpu()  # Gerçek GPU var mı?
        self._sim_load = 40.0             # Simülasyon başlangıç yük değeri

    def _check_gpu(self) -> bool:
        """GPUtil kütüphanesi yüklüyse True döner."""
        try:
            import GPUtil                # İsteğe bağlı kütüphane
            return len(GPUtil.getGPUs()) > 0  # GPU listesi doluysa True
        except ImportError:
            return False                 # Kütüphane yoksa False

    def _simulate(self) -> dict:
        """Gerçekçi GPU simülasyonu: yük dalgalanması ile üretilir."""
        cpu_usage = psutil.cpu_percent(interval=None)          # CPU yükünü referans al
        self._sim_load += random.uniform(-5, 5)                # Küçük dalgalanma ekle
        self._sim_load  = max(20, min(95, self._sim_load))     # 20–95 aralığında tut
        gpu_load = round((self._sim_load + cpu_usage * 0.3) / 1.3, 1)  # Ağırlıklı yük
        gpu_temp = round(38 + gpu_load * 0.52 + random.uniform(-2, 2), 1)  # Sıcaklık
        return {"usage": gpu_load, "temperature": gpu_temp, "memory_used": round(gpu_load * 0.08, 2)}

    def collect(self) -> dict:
        """GPU verisini toplar; donanım yoksa simülasyon kullanır."""
        if self._gpu_available:
            try:
                import GPUtil
                gpu  = GPUtil.getGPUs()[0]                   # İlk GPU'yu al
                data = {
                    "usage"      : round(gpu.load * 100, 1), # Kullanım (%)
                    "temperature": round(gpu.temperature, 1),# Sıcaklık (°C)
                    "memory_used": round(gpu.memoryUsed / 1024, 2),  # VRAM (GB)
                }
            except Exception:
                data = self._simulate()   # Hata olursa simülasyona düş
        else:
            data = self._simulate()       # Kütüphane yoksa simülasyon
        self._add_to_history(data)        # Geçmişe kaydet
        return data                       # Veriyi döndür


# ───────────────────────────────────────────────
# RAM MONİTÖR SINIFI - BaseMonitor'dan türetildi
# ───────────────────────────────────────────────
class RAMMonitor(BaseMonitor):
    """RAM kullanımını izler."""

    def __init__(self):
        super().__init__("RAM Monitor")   # Üst sınıfı başlat

    def collect(self) -> dict:
        """Anlık RAM kullanım bilgisini toplar."""
        mem  = psutil.virtual_memory()    # Sanal bellek bilgisini al
        data = {
            "usage"     : mem.percent,                         # Kullanım yüzdesi
            "used_gb"   : round(mem.used  / 1e9, 2),          # Kullanılan (GB)
            "total_gb"  : round(mem.total / 1e9, 2),          # Toplam (GB)
            "available" : round(mem.available / 1e9, 2),      # Boş (GB)
        }
        self._add_to_history(data)   # Geçmişe kaydet
        return data                  # Veriyi döndür


# ───────────────────────────────────────────────
# FPS MONİTÖR SINIFI - BaseMonitor'dan türetildi
# ───────────────────────────────────────────────
class FPSMonitor(BaseMonitor):
    """Oyun FPS değerini simüle eder (gerçek uygulamada oyun API'sine bağlanır)."""

    def __init__(self):
        super().__init__("FPS Monitor")   # Üst sınıfı başlat
        self._base_fps = 120.0            # Başlangıç FPS değeri
        self._frame_times = []            # Frame sürelerini tutar (kayan pencere)

    def collect(self) -> dict:
        """CPU/GPU yüküne bağlı gerçekçi FPS simülasyonu üretir."""
        cpu = psutil.cpu_percent(interval=None)        # Anlık CPU yükü
        # CPU yükseldikçe FPS düşer; gürültü ile gerçekçilik sağlanır
        fps = self._base_fps - (cpu * 0.6) + random.uniform(-8, 8)
        fps = max(15, min(165, fps))                   # FPS 15–165 arasında sınırla
        self._base_fps += random.uniform(-2, 2)        # Temel FPS hafifçe dalgalansın
        self._base_fps  = max(60, min(144, self._base_fps))  # Temel 60–144 arasında

        frame_time = round(1000 / fps, 2) if fps > 0 else 0  # ms cinsinden frame süresi
        self._frame_times.append(frame_time)
        if len(self._frame_times) > 60:               # Son 60 frame'i tut
            self._frame_times.pop(0)

        data = {
            "fps"       : round(fps, 1),              # Anlık FPS
            "frame_time": frame_time,                 # Frame süresi (ms)
            "avg_fps"   : round(sum(self._frame_times) and 1000 /
                          (sum(self._frame_times) / len(self._frame_times)), 1),  # Ort. FPS
        }
        self._add_to_history(data)   # Geçmişe kaydet
        return data                  # Veriyi döndür


# ───────────────────────────────────────────────
# DİSK MONİTÖR SINIFI - BaseMonitor'dan türetildi
# ───────────────────────────────────────────────
class DiskMonitor(BaseMonitor):
    """Disk okuma/yazma hızlarını ve doluluk oranını izler."""

    def __init__(self):
        super().__init__("Disk Monitor")  # Üst sınıfı başlat
        self._last_io = psutil.disk_io_counters()  # Önceki IO sayaçları
        self._last_time = time.time()              # Önceki ölçüm zamanı

    def collect(self) -> dict:
        """Disk doluluk ve anlık IO hız bilgisini toplar."""
        disk    = psutil.disk_usage("/")           # Kök dizin disk kullanımı
        io      = psutil.disk_io_counters()        # Güncel IO sayaçları
        elapsed = time.time() - self._last_time    # Geçen süre (saniye)

        # Saniyedeki okuma/yazma miktarını MB cinsinden hesapla
        read_mb  = round((io.read_bytes  - self._last_io.read_bytes)  / 1e6 / elapsed, 2)
        write_mb = round((io.write_bytes - self._last_io.write_bytes) / 1e6 / elapsed, 2)

        self._last_io   = io            # Sayaçları güncelle
        self._last_time = time.time()   # Zamanı güncelle

        data = {
            "usage"   : disk.percent,                      # Doluluk yüzdesi
            "read_mb" : max(0, read_mb),                   # Okuma hızı (MB/s)
            "write_mb": max(0, write_mb),                  # Yazma hızı (MB/s)
            "free_gb" : round(disk.free / 1e9, 1),         # Boş alan (GB)
        }
        self._add_to_history(data)   # Geçmişe kaydet
        return data                  # Veriyi döndür
