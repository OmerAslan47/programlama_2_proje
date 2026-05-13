# =============================================================================
# monitor.py - Veri Toplama Modülü
# Kastamonu Üniversitesi Tosya MYO - Programlama II Dönem Projesi
# Bu modül; FPS, CPU, GPU, RAM, disk ve ağ verilerini toplar.
# =============================================================================

import time           # Zaman işlemleri için (timestamp, sleep)
import random         # Simüle edilmiş sensör verisi üretmek için
import platform       # İşletim sistemi bilgisi almak için
import os             # Ortam değişkenleri ve dosya yolları için
from datetime import datetime  # Tarih/saat damgası oluşturmak için

# psutil kütüphanesi kurulu değilse sahte veri üretmek için bayrak
try:
    import psutil     # CPU, RAM, disk, ağ gibi sistem bilgisi kütüphanesi
    PSUTIL_AVAILABLE = True   # Kütüphane varsa True yap
except ImportError:
    PSUTIL_AVAILABLE = False  # Kütüphane yoksa False yap (simülasyon moduna geç)


# =============================================================================
# TEMEL SINIF: SensorBase
# Tüm sensör sınıflarının miras alacağı ana sınıf (Kalıtım temeli)
# =============================================================================
class SensorBase:
    """Tüm sensör sınıfları için temel (base) sınıf."""

    def __init__(self, sensor_name: str):
        self._name = sensor_name          # Sensör adı (kapsülleme: _ ile koruma altında)
        self._readings = []               # Okunan değerlerin listesi (kapsülleme)
        self._last_value = None           # Son okunan değer
        self._unit = ""                   # Birimi (°C, %, FPS vs.)
        self._is_active = True            # Sensör aktif mi?

    # ---------- Property (Getter/Setter) - Kapsülleme örneği ----------

    @property
    def name(self):
        """Sensör adını döndür (salt okunur property)."""
        return self._name                 # Dışarıdan okumaya izin ver

    @property
    def last_value(self):
        """Son okunan değeri döndür."""
        return self._last_value

    @property
    def unit(self):
        """Birimi döndür."""
        return self._unit

    @property
    def readings(self):
        """Tüm okuma geçmişini döndür (kopya olarak)."""
        return list(self._readings)       # Orijinal listeyi korumak için kopya döndür

    @property
    def is_active(self):
        """Sensörün aktif olup olmadığını döndür."""
        return self._is_active

    # ---------- Temel Metotlar ----------

    def read(self):
        """Alt sınıflar tarafından override edilmesi gereken okuma metodu."""
        raise NotImplementedError("read() metodu alt sınıfta tanımlanmalıdır!")

    def _save_reading(self, value, timestamp=None):
        """Okunan değeri kaydet. Alt sınıflar tarafından çağrılır."""
        if timestamp is None:
            timestamp = datetime.now()    # Zaman damgası yoksa şimdiki zamanı kullan
        entry = {
            "timestamp": timestamp,       # Ölçüm zamanı
            "value": value,               # Ölçülen değer
            "unit": self._unit            # Birimi
        }
        self._readings.append(entry)      # Listeye ekle
        self._last_value = value          # Son değeri güncelle

        # Bellek tasarrufu: son 1000 kaydı tut, eskiyi sil
        if len(self._readings) > 1000:
            self._readings.pop(0)         # En eski kaydı sil

    def get_average(self):
        """Tüm okumalar için ortalama hesapla."""
        if not self._readings:            # Hiç okuma yoksa
            return 0.0
        values = [r["value"] for r in self._readings]  # Sadece değerleri al
        return sum(values) / len(values)  # Aritmetik ortalama

    def get_max(self):
        """Maksimum değeri döndür."""
        if not self._readings:
            return 0.0
        return max(r["value"] for r in self._readings)

    def get_min(self):
        """Minimum değeri döndür."""
        if not self._readings:
            return 0.0
        return min(r["value"] for r in self._readings)

    def reset(self):
        """Tüm okuma geçmişini sıfırla."""
        self._readings = []               # Listeyi boşalt
        self._last_value = None           # Son değeri sıfırla

    def __str__(self):
        """Nesneyi yazdırınca anlamlı bir çıktı ver."""
        return f"[{self._name}] Son Değer: {self._last_value} {self._unit}"

    def __repr__(self):
        """Geliştirici için resmi temsil."""
        return f"SensorBase(name='{self._name}', active={self._is_active})"


# =============================================================================
# FPS SENSÖRÜ - SensorBase'den kalıtım alır
# Oyun karesi sayısını (Frame Per Second) simüle eder
# =============================================================================
class FPSSensor(SensorBase):
    """FPS (Kare/Saniye) ölçüm sensörü."""

    def __init__(self):
        super().__init__("FPS Sensörü")   # Üst sınıf başlatıcısını çağır
        self._unit = "FPS"                # Birim: Kare/saniye
        self._target_fps = 60             # Hedef FPS değeri (kapsülleme)
        self._game_load = 0.5             # Oyunun sistem yükü katsayısı (0.0-1.0)

    @property
    def target_fps(self):
        """Hedef FPS değerini döndür."""
        return self._target_fps

    @target_fps.setter
    def target_fps(self, value):
        """Hedef FPS'i güncelle (doğrulama ile)."""
        if 1 <= value <= 360:             # Geçerli aralık kontrolü
            self._target_fps = value
        else:
            raise ValueError("Hedef FPS 1 ile 360 arasında olmalıdır!")

    def set_game_load(self, load: float):
        """Oyun yükünü ayarla (0.0 = hafif, 1.0 = ağır sahne)."""
        self._game_load = max(0.0, min(1.0, load))  # 0-1 arasına sıkıştır

    def read(self):
        """Anlık FPS değerini oku (simülasyon)."""
        # Temel FPS: hedef × (1 - yük etkisi)
        base_fps = self._target_fps * (1.0 - self._game_load * 0.4)

        # Gerçekçi dalgalanma ekle: ±8 FPS rastgele sapma
        noise = random.uniform(-8, 8)
        fps_value = max(5, base_fps + noise)  # En az 5 FPS olsun

        fps_value = round(fps_value, 1)   # 1 ondalık basamağa yuvarla
        self._save_reading(fps_value)     # Üst sınıftaki kayıt metodunu çağır
        return fps_value

    def get_stability_score(self):
        """FPS kararlılık skoru hesapla (0-100 arası)."""
        if len(self._readings) < 5:       # Yeterli veri yoksa
            return 100.0
        values = [r["value"] for r in self._readings[-20:]]  # Son 20 okuma
        avg = sum(values) / len(values)
        # Standart sapma benzeri hesaplama
        variance = sum((v - avg) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5         # Karekök al
        score = max(0, 100 - std_dev * 2) # Sapma arttıkça skor düşer
        return round(score, 1)


# =============================================================================
# CPU SICAKLIK SENSÖRÜ - SensorBase'den kalıtım alır
# =============================================================================
class CPUTemperatureSensor(SensorBase):
    """CPU sıcaklık sensörü."""

    def __init__(self):
        super().__init__("CPU Sıcaklık")  # Üst sınıf başlatıcısı
        self._unit = "°C"                 # Derece Celsius
        self._base_temp = 42.0            # Bekleme durumu sıcaklığı
        self._load_factor = 0.0           # CPU yük katsayısı (0.0-1.0)
        self._warning_threshold = 80.0    # Uyarı sıcaklığı eşiği
        self._critical_threshold = 95.0   # Kritik sıcaklık eşiği

    def set_load(self, load: float):
        """CPU yükünü ayarla."""
        self._load_factor = max(0.0, min(1.0, load))  # 0-1 arası sıkıştır

    def read(self):
        """CPU sıcaklığını oku."""
        if PSUTIL_AVAILABLE:
            try:
                temps = psutil.sensors_temperatures()  # Gerçek sıcaklık dene
                if temps and "coretemp" in temps:
                    cpu_temp = temps["coretemp"][0].current  # İlk çekirdek
                    self._save_reading(round(cpu_temp, 1))
                    return round(cpu_temp, 1)
            except Exception:
                pass                       # Başarısız olursa simülasyona geç

        # Simülasyon: yüke göre sıcaklık hesapla
        load_temp = self._base_temp + (self._load_factor * 45)  # Yük etkisi
        noise = random.uniform(-2.0, 2.0)  # ±2°C gerçekçi dalgalanma
        temp = round(max(30, load_temp + noise), 1)
        self._save_reading(temp)
        return temp

    def get_status(self):
        """Sıcaklık durumunu döndür: normal / uyarı / kritik."""
        if self._last_value is None:
            return "bilinmiyor"
        if self._last_value >= self._critical_threshold:
            return "kritik"               # 95°C üzeri tehlikeli
        elif self._last_value >= self._warning_threshold:
            return "uyarı"                # 80°C üzeri uyarı
        else:
            return "normal"               # Normal çalışma aralığı


# =============================================================================
# GPU SICAKLIK SENSÖRÜ - CPUTemperatureSensor'dan kalıtım alır
# GPU'nun ayrı eşik değerleri ve yük profili vardır
# =============================================================================
class GPUTemperatureSensor(CPUTemperatureSensor):
    """GPU sıcaklık sensörü (CPU sensöründen kalıtım alır)."""

    def __init__(self):
        super().__init__()                # CPU sensörünü başlat
        self._name = "GPU Sıcaklık"       # Adı override et
        self._base_temp = 38.0            # GPU bekleme sıcaklığı biraz daha düşük
        self._warning_threshold = 83.0    # GPU için farklı uyarı eşiği
        self._critical_threshold = 92.0   # GPU için farklı kritik eşik
        self._vram_load = 0.0             # Video RAM yük katsayısı

    def set_vram_load(self, load: float):
        """VRAM yükünü ayarla."""
        self._vram_load = max(0.0, min(1.0, load))

    def read(self):
        """GPU sıcaklığını oku (psutil GPU desteği sınırlı, genellikle simülasyon)."""
        # GPU + VRAM yükü birlikte sıcaklığı etkiler
        combined_load = (self._load_factor * 0.7) + (self._vram_load * 0.3)
        load_temp = self._base_temp + (combined_load * 50)  # Yük etkisi
        noise = random.uniform(-1.5, 1.5)  # ±1.5°C dalgalanma
        temp = round(max(28, load_temp + noise), 1)
        self._save_reading(temp)
        return temp


# =============================================================================
# CPU KULLANIM SENSÖRÜ - SensorBase'den kalıtım alır
# =============================================================================
class CPUUsageSensor(SensorBase):
    """CPU kullanım yüzdesi sensörü."""

    def __init__(self):
        super().__init__("CPU Kullanımı")
        self._unit = "%"                  # Yüzde birimi
        self._base_usage = 15.0           # Boşta CPU kullanımı
        self._game_boost = 0.0            # Oyun kaynaklı ek yük

    def set_game_boost(self, boost: float):
        """Oyun yükünü ayarla."""
        self._game_boost = max(0.0, min(85.0, boost))  # 0-85% arasında tut

    def read(self):
        """CPU kullanımını oku."""
        if PSUTIL_AVAILABLE:
            try:
                # interval=None: son ölçümden bu yana olan değeri al (bloklama yok)
                usage = psutil.cpu_percent(interval=None)
                self._save_reading(round(usage, 1))
                return round(usage, 1)
            except Exception:
                pass

        # Simülasyon
        usage = self._base_usage + self._game_boost + random.uniform(-5, 5)
        usage = round(max(0, min(100, usage)), 1)  # 0-100% arasına sıkıştır
        self._save_reading(usage)
        return usage


# =============================================================================
# RAM KULLANIM SENSÖRÜ - SensorBase'den kalıtım alır
# =============================================================================
class RAMUsageSensor(SensorBase):
    """RAM kullanımı sensörü."""

    def __init__(self):
        super().__init__("RAM Kullanımı")
        self._unit = "%"
        self._base_usage = 30.0           # Sistem bekleme RAM kullanımı
        self._game_usage = 0.0            # Oyun için kullanılan ek RAM

    def set_game_usage(self, usage: float):
        """Oyun RAM kullanımını ayarla."""
        self._game_usage = max(0.0, min(60.0, usage))

    def read(self):
        """RAM kullanımını oku."""
        if PSUTIL_AVAILABLE:
            try:
                ram = psutil.virtual_memory()  # Sanal bellek bilgisi
                usage = ram.percent           # Kullanım yüzdesi
                self._save_reading(round(usage, 1))
                return round(usage, 1)
            except Exception:
                pass

        # Simülasyon
        usage = self._base_usage + self._game_usage + random.uniform(-3, 3)
        usage = round(max(0, min(100, usage)), 1)
        self._save_reading(usage)
        return usage

    def get_used_gb(self):
        """Kullanılan RAM miktarını GB cinsinden döndür."""
        if PSUTIL_AVAILABLE:
            try:
                ram = psutil.virtual_memory()
                return round(ram.used / (1024 ** 3), 2)  # Byte → GB dönüşümü
            except Exception:
                pass
        return round(self._last_value * 0.16, 2) if self._last_value else 0.0  # 16GB simülasyon

    def get_total_gb(self):
        """Toplam RAM miktarını GB cinsinden döndür."""
        if PSUTIL_AVAILABLE:
            try:
                ram = psutil.virtual_memory()
                return round(ram.total / (1024 ** 3), 2)
            except Exception:
                pass
        return 16.0                       # Simülasyon: 16GB varsayılan


# =============================================================================
# DİSK KULLANIM SENSÖRÜ - SensorBase'den kalıtım alır
# =============================================================================
class DiskUsageSensor(SensorBase):
    """Disk I/O ve doluluk sensörü."""

    def __init__(self, path="/"):
        super().__init__("Disk Kullanımı")
        self._unit = "%"
        self._path = path                 # İzlenecek disk yolu
        self._base_io = 5.0               # Baz I/O aktivitesi

    def read(self):
        """Disk doluluk yüzdesini oku."""
        if PSUTIL_AVAILABLE:
            try:
                disk = psutil.disk_usage(self._path)   # Belirtilen yol için
                usage = disk.percent
                self._save_reading(round(usage, 1))
                return round(usage, 1)
            except Exception:
                pass

        # Simülasyon: disk doluluk sabit gibi davranır
        usage = round(65.0 + random.uniform(-1, 1), 1)
        self._save_reading(usage)
        return usage

    def get_io_activity(self):
        """Disk I/O aktivitesini oku (MB/s)."""
        if PSUTIL_AVAILABLE:
            try:
                io = psutil.disk_io_counters()         # I/O sayaçları
                # Basit simülasyon: gerçek I/O hesaplaması iki ölçüm arası fark gerektirir
                return round(random.uniform(0.5, 50.0), 2)
            except Exception:
                pass
        return round(self._base_io + random.uniform(0, 20), 2)


# =============================================================================
# AĞ SENSÖRÜ - SensorBase'den kalıtım alır
# =============================================================================
class NetworkSensor(SensorBase):
    """Ağ bant genişliği kullanımı sensörü."""

    def __init__(self):
        super().__init__("Ağ Kullanımı")
        self._unit = "Mbps"               # Megabit/saniye
        self._prev_bytes_sent = 0         # Önceki gönderilen byte (delta için)
        self._prev_bytes_recv = 0         # Önceki alınan byte (delta için)
        self._prev_time = time.time()     # Önceki ölçüm zamanı

    def read(self):
        """Anlık ağ hızını oku (Mbps)."""
        if PSUTIL_AVAILABLE:
            try:
                net = psutil.net_io_counters()     # Ağ I/O sayaçları
                current_time = time.time()
                elapsed = current_time - self._prev_time  # Geçen süre

                if elapsed > 0 and self._prev_bytes_recv > 0:
                    # Byte farkını bit/saniye'ye çevir, sonra Mbps yap
                    recv_speed = (net.bytes_recv - self._prev_bytes_recv) * 8 / elapsed / 1_000_000
                    send_speed = (net.bytes_sent - self._prev_bytes_sent) * 8 / elapsed / 1_000_000
                    total_speed = round(recv_speed + send_speed, 2)
                else:
                    total_speed = 0.0

                # Bir sonraki ölçüm için değerleri güncelle
                self._prev_bytes_recv = net.bytes_recv
                self._prev_bytes_sent = net.bytes_sent
                self._prev_time = current_time

                self._save_reading(total_speed)
                return total_speed
            except Exception:
                pass

        # Simülasyon: oyun sırasında ortalama ağ kullanımı
        speed = round(random.uniform(0.5, 25.0), 2)
        self._save_reading(speed)
        return speed


# =============================================================================
# PİL SENSÖRÜ - SensorBase'den kalıtım alır (laptop desteği)
# =============================================================================
class BatterySensor(SensorBase):
    """Pil durumu sensörü (laptop için)."""

    def __init__(self):
        super().__init__("Pil Durumu")
        self._unit = "%"
        self._is_charging = False         # Şarj durumu

    def read(self):
        """Pil yüzdesini oku."""
        if PSUTIL_AVAILABLE:
            try:
                battery = psutil.sensors_battery()    # Pil bilgisi
                if battery:
                    self._is_charging = battery.power_plugged  # Fişe takılı mı?
                    percent = round(battery.percent, 1)
                    self._save_reading(percent)
                    return percent
            except Exception:
                pass

        # Masaüstü veya veri yoksa 100% döndür
        self._save_reading(100.0)
        return 100.0

    def is_charging(self):
        """Şarj durumunu döndür."""
        return self._is_charging


# =============================================================================
# OYUN PROFİLİ YÖNETİCİSİ
# Farklı oyun senaryolarına göre sensör yüklerini ayarlar
# =============================================================================
class GameProfileManager:
    """Oyun profili yöneticisi – farklı senaryolar için yük profilleri."""

    # Sınıf düzeyinde tanımlanan profil sözlüğü (tüm nesneler paylaşır)
    PROFILES = {
        "hafif": {                        # Basit 2D oyunlar
            "fps_target": 120,
            "cpu_usage": 25.0,
            "gpu_load": 0.3,
            "ram_usage": 20.0,
            "fps_load": 0.2,
            "label": "Hafif (2D/Indie)"
        },
        "orta": {                         # Orta grafik ayarlı 3D oyunlar
            "fps_target": 60,
            "cpu_usage": 55.0,
            "gpu_load": 0.65,
            "ram_usage": 45.0,
            "fps_load": 0.5,
            "label": "Orta (3D Oyun)"
        },
        "agir": {                         # AAA oyunlar, yüksek ayarlar
            "fps_target": 60,
            "cpu_usage": 80.0,
            "gpu_load": 0.88,
            "ram_usage": 65.0,
            "fps_load": 0.75,
            "label": "Ağır (AAA / Yüksek Ayar)"
        },
        "stres": {                        # Stres testi / benchmark
            "fps_target": 30,
            "cpu_usage": 95.0,
            "gpu_load": 0.98,
            "ram_usage": 85.0,
            "fps_load": 0.95,
            "label": "Stres Testi"
        }
    }

    def __init__(self):
        self._current_profile = "orta"    # Varsayılan profil

    @property
    def current_profile(self):
        return self._current_profile

    def apply_profile(self, profile_name: str, sensor_group):
        """Profili sensör grubuna uygula."""
        if profile_name not in self.PROFILES:
            raise ValueError(f"Geçersiz profil: {profile_name}")

        self._current_profile = profile_name
        p = self.PROFILES[profile_name]   # Profil sözlüğünü al

        # Her sensöre profil değerini uygula
        sensor_group.fps_sensor.target_fps = p["fps_target"]
        sensor_group.fps_sensor.set_game_load(p["fps_load"])
        sensor_group.cpu_usage_sensor.set_game_boost(p["cpu_usage"])
        sensor_group.gpu_temp_sensor.set_load(p["gpu_load"])
        sensor_group.ram_sensor.set_game_usage(p["ram_usage"])
        sensor_group.cpu_temp_sensor.set_load(p["gpu_load"] * 0.8)  # CPU ısı katsayısı

    def get_profile_info(self, profile_name: str) -> dict:
        """Profil bilgilerini döndür."""
        return self.PROFILES.get(profile_name, {})

    @staticmethod
    def list_profiles() -> list:
        """Mevcut profil isimlerini listele."""
        return list(GameProfileManager.PROFILES.keys())


# =============================================================================
# SENSÖR GRUBU - Tüm sensörleri tek çatı altında toplar
# =============================================================================
class SensorGroup:
    """Tüm sensörleri bir arada yöneten konteyner sınıf."""

    def __init__(self):
        # Her sensör nesnesi oluşturuluyor
        self.fps_sensor = FPSSensor()                  # FPS sensörü
        self.cpu_temp_sensor = CPUTemperatureSensor()  # CPU sıcaklık
        self.gpu_temp_sensor = GPUTemperatureSensor()  # GPU sıcaklık
        self.cpu_usage_sensor = CPUUsageSensor()       # CPU kullanım
        self.ram_sensor = RAMUsageSensor()             # RAM kullanım
        self.disk_sensor = DiskUsageSensor()           # Disk doluluk
        self.network_sensor = NetworkSensor()          # Ağ hızı
        self.battery_sensor = BatterySensor()          # Pil durumu

        # Tüm sensörleri listeye ekle (döngüsel işlemler için)
        self._all_sensors = [
            self.fps_sensor,
            self.cpu_temp_sensor,
            self.gpu_temp_sensor,
            self.cpu_usage_sensor,
            self.ram_sensor,
            self.disk_sensor,
            self.network_sensor,
            self.battery_sensor
        ]

    def read_all(self) -> dict:
        """Tüm sensörlerden veri oku ve sözlük olarak döndür."""
        data = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),  # Saat:Dakika:Saniye
            "fps": self.fps_sensor.read(),
            "cpu_temp": self.cpu_temp_sensor.read(),
            "gpu_temp": self.gpu_temp_sensor.read(),
            "cpu_usage": self.cpu_usage_sensor.read(),
            "ram_usage": self.ram_sensor.read(),
            "ram_used_gb": self.ram_sensor.get_used_gb(),
            "ram_total_gb": self.ram_sensor.get_total_gb(),
            "disk_usage": self.disk_sensor.read(),
            "disk_io": self.disk_sensor.get_io_activity(),
            "network_speed": self.network_sensor.read(),
            "battery": self.battery_sensor.read(),
            "battery_charging": self.battery_sensor.is_charging(),
            "fps_stability": self.fps_sensor.get_stability_score(),
            "cpu_status": self.cpu_temp_sensor.get_status(),
            "gpu_status": self.gpu_temp_sensor.get_status()
        }
        return data

    def reset_all(self):
        """Tüm sensörlerin geçmişini sıfırla."""
        for sensor in self._all_sensors:
            sensor.reset()               # Her sensörü sıfırla

    def get_system_info(self) -> dict:
        """Sistem bilgilerini topla."""
        info = {
            "os": platform.system(),                   # İşletim sistemi
            "os_version": platform.version(),          # OS sürümü
            "processor": platform.processor(),         # İşlemci adı
            "python_version": platform.python_version(), # Python sürümü
            "psutil_available": PSUTIL_AVAILABLE       # Gerçek mi simülasyon mu?
        }
        if PSUTIL_AVAILABLE:
            try:
                info["cpu_count_physical"] = psutil.cpu_count(logical=False)  # Fiziksel çekirdek
                info["cpu_count_logical"] = psutil.cpu_count(logical=True)    # Mantıksal çekirdek
                ram = psutil.virtual_memory()
                info["total_ram_gb"] = round(ram.total / (1024 ** 3), 1)     # GB cinsinden
            except Exception:
                pass
        return info
