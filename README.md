# ⚡ GameSpy Monitor

**Kastamonu Üniversitesi Tosya Meslek Yüksekokulu**  
**Programlama II – Dönem Sonu Projesi**

---

## 📌 Proje Özeti

GameSpy Monitor, oyun oynarken sistemin **FPS, CPU/GPU sıcaklığı, RAM/CPU kullanımı, disk doluluk, ağ hızı ve pil durumu** gibi kritik performans metriklerini gerçek zamanlı olarak toplayan, analiz eden ve değerlendiren bir **Python masaüstü uygulamasıdır**.

Proje tamamen **Nesne Tabanlı Programlama (OOP)** prensiplerine (Kalıtım, Kapsülleme, Soyutlama) uygun olarak geliştirilmiştir. Arayüz için Python'ın yerleşik `tkinter` kütüphanesi kullanılmıştır.

---

## 🖼️ Özellikler

| Özellik | Açıklama |
|---|---|
| Gerçek Zamanlı İzleme | 1.5 saniyede bir tüm sensörler okunur |
| 4 Oyun Profili | Hafif, Orta, Ağır, Stres profilleri |
| Ağırlıklı Puanlama | FPS, sıcaklık, kullanım verileriyle 0-100 puan |
| Canlı Grafikler | FPS, CPU ve GPU sıcaklığı için mini çizgi grafikler |
| Uyarı Sistemi | Eşik değerleri aşıldığında anlık uyarı |
| Oturum Raporu | Ortalamalar ve JSON dışa aktarım |
| Karanlık Tema | Profesyonel neon-karanlık arayüz |

---

## 📁 Proje Yapısı

```
gamespy-monitor/
│
├── main.py          # Ana çalışma dosyası – GUI ve uygulama yönetimi
├── monitor.py       # Veri toplama sınıfları (SensorBase ve alt sınıflar)
├── analyzer.py      # Değerlendirme ve analiz sınıfları
├── session_report.json  # (Çalışma sonrası oluşur) Oturum raporu
└── README.md        # Bu dosya
```

---

## 🚀 Kurulum ve Çalıştırma

### Gereksinimler

- Python 3.8 veya üzeri
- `psutil` kütüphanesi (opsiyonel – yoksa simülasyon modunda çalışır)
- `tkinter` (Python ile birlikte gelir)

### Adımlar

```bash
# 1. Repoyu klonla
git clone https://github.com/KULLANICI_ADI/gamespy-monitor.git
cd gamespy-monitor

# 2. (Opsiyonel) psutil kur – gerçek sistem verisi için
pip install psutil

# 3. Uygulamayı çalıştır
python main.py
```

> **Not:** `psutil` kurulu değilse uygulama **simülasyon modunda** çalışır ve gerçekçi rastgele veriler üretir. Tüm özellikler kullanılabilir.

---

## 🎮 Kullanım

1. **Profil Seç:** Araç çubuğundan oyun profilini seçin (Hafif / Orta / Ağır / Stres).
2. **Başlat:** `▶ BAŞLAT` butonuna basın – izleme başlar.
3. **İzle:** Metrik kartlarını, canlı grafikleri ve uyarı panelini takip edin.
4. **Rapor:** `📋 RAPOR` butonu ile oturum özetini ve sistem notunu görün.
5. **Kaydet:** Rapor penceresinden JSON olarak dışa aktarın.
6. **Sıfırla:** `↺ SIFIRLA` ile yeni bir oturum başlatın.

---

## 🏗️ OOP Mimarisi (Özet)

```
SensorBase (Temel Sınıf)
├── FPSSensor
├── CPUTemperatureSensor
│   └── GPUTemperatureSensor   ← Kalıtım
├── CPUUsageSensor
├── RAMUsageSensor
├── DiskUsageSensor
├── NetworkSensor
└── BatterySensor

AnalyzerBase (Temel Sınıf)
├── FPSAnalyzer
├── TemperatureAnalyzer
├── UsageAnalyzer
├── AlertManager
└── ReportGenerator

GameProfileManager            ← Profil yönetimi
SensorGroup                   ← Tüm sensörleri kapsar
SystemEvaluator               ← Ağırlıklı genel puan
GameMonitorApp                ← GUI ana sınıfı
```

---

## 📊 Puanlama Sistemi

Sistem puanı, aşağıdaki ağırlıklı ortalama ile hesaplanır:

| Metrik | Ağırlık |
|---|---|
| FPS | %30 |
| CPU Sıcaklığı | %15 |
| GPU Sıcaklığı | %15 |
| CPU Kullanımı | %15 |
| RAM Kullanımı | %15 |
| Disk Doluluk | %5 |
| Ağ Hızı | %5 |

---

## 👤 Geliştiriciler

| Ad Soyad | [Ömer Aslan] |
| Öğrenci No | [255815028] |

|---
| Ad Soyad | [Kadir Baran Akbaba] |
| Öğrenci No | [255815022] |

----
| Ad Soyad | [Emirhan Çukurkaş] |
| Öğrenci No | [255815015] |

