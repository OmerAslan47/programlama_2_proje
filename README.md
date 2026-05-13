# 🎮 GameMonitor — Oyun Performans İzleme Aracı

> Kastamonu Üniversitesi Tosya MYO · Programlama II · Dönem Sonu Projesi

---

## 📌 Proje Hakkında

**GameMonitor**, oyun oynarken sistemin gerçek zamanlı performans değerlerini (FPS, CPU/GPU sıcaklık ve kullanım, RAM, Disk) toplayan, bu verilerin ortalamasını hesaplayarak sistemi puanlayan ve sonuçları profesyonel bir grafiksel arayüzde gösteren bir Python uygulamasıdır.

---

## 🗂️ Dosya Yapısı

```
GameMonitor/
├── main.py        # GUI arayüzü ve uygulama giriş noktası
├── monitor.py     # Veri toplama sınıfları (OOP)
├── analyzer.py    # Analiz ve puanlama mantığı (OOP)
├── requirements.txt
└── README.md
```

---

## 🛠️ Kurulum

```bash
pip install psutil
# İsteğe bağlı (gerçek GPU verisi için):
pip install gputil
```

Çalıştırmak için:
```bash
python main.py
```

---

## 🧩 OOP Mimarisi

| Sınıf | Dosya | Açıklama |
|---|---|---|
| `BaseMonitor` | monitor.py | Soyut temel sınıf |
| `CPUMonitor` | monitor.py | CPU verisi, BaseMonitor'dan türetildi |
| `GPUMonitor` | monitor.py | GPU verisi, BaseMonitor'dan türetildi |
| `RAMMonitor` | monitor.py | RAM verisi, BaseMonitor'dan türetildi |
| `FPSMonitor` | monitor.py | FPS simülasyonu, BaseMonitor'dan türetildi |
| `DiskMonitor` | monitor.py | Disk I/O, BaseMonitor'dan türetildi |
| `PerformanceScore` | analyzer.py | Eşik değer puanlama |
| `SystemAnalyzer` | analyzer.py | Ağırlıklı genel skor hesaplama |
| `GameMonitorApp` | main.py | Tkinter GUI yöneticisi |

---

## 📊 İzlenen Metrikler

- 🎯 **FPS** — Oyun kare hızı (simülasyon)
- 🖥 **CPU Kullanımı** — Anlık işlemci yüzdesi
- 🌡 **CPU Sıcaklığı** — Sensör veya simülasyon
- 🎮 **GPU Kullanımı** — GPUtil veya simülasyon
- 🌡 **GPU Sıcaklığı** — GPUtil veya simülasyon
- 💾 **RAM Kullanımı** — Bellek doluluk yüzdesi
- 💿 **Disk I/O** — Okuma/yazma hızı (MB/s)

---

## 🏫 Bilgiler

- **Üniversite:** Kastamonu Üniversitesi
- **Yüksekokul:** Tosya Meslek Yüksekokulu
- **Ders:** Programlama II
- **Dil:** Python 3.x
- **Arayüz:** tkinter (standart kütüphane)

## Geliştiriciler

| Ad Soyad | [Ömer Aslan] | | Öğrenci No | [255815028] |  
| Ad Soyad | [Kadir Baran Akbaba] | | Öğrenci No | [255815022] |  
| Ad Soyad | [Emirhan Çukurkaş] | | Öğrenci No | [255815015] |