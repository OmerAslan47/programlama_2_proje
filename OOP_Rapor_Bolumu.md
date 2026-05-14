# OOP Yapısı ve Modüllerin Açıklaması
### (5 Sayfalık Teknik Rapor — İlgili Bölüm)

---

## 1. Modüler Yapı Genel Bakış

Proje üç ayrı Python dosyasına bölünmüştür. Her dosya tek bir sorumluluğu üstlenir
(*Single Responsibility Principle*). Dosyalar arası iletişim Python'un `import`
mekanizmasıyla sağlanır; böylece modüller birbirinden bağımsız test edilebilir.

| Dosya | Sorumluluk |
|---|---|
| `monitor.py` | Donanım verisi toplama sınıfları |  Ömer Aslan.        |
| `analyzer.py` | Veri analizi ve puanlama sınıfları |  Emirhan Çukurkaş|
| `main.py` | GUI yönetimi ve uygulama döngüsü | Baran Akbaba           |

---

## 2. monitor.py — Veri Toplama Modülü

### 2.1 BaseMonitor (Temel Sınıf)

- **Tür:** Soyut temel sınıf (abstract base class)
- **OOP İlkesi:** Kalıtım (Inheritance) — diğer tüm monitörler buradan türetilir.
- **Kapsülleme:** `_name`, `_history`, `_start_time` değişkenleri alt çizgi (`_`) ile
  korumalı (protected) olarak tanımlanmıştır; doğrudan dışarıdan değiştirilemez.
- **Temel Metodlar:**
  - `collect()` → Alt sınıfların override etmesi zorunlu; doğrudan çağrılırsa
    `NotImplementedError` fırlatır (Polimorfizm kapısı).
  - `_add_to_history(data)` → Her ölçüm saat damgasıyla birlikte `_history`
    listesine eklenir; bellek taşmasını önlemek için liste 300 kayıtla sınırlıdır.
  - `get_average(key)` → Geçmişteki belirli bir anahtarın aritmetik ortalamasını
    hesaplar; veri yoksa 0.0 döner.

### 2.2 CPUMonitor (BaseMonitor'dan türetildi)

- `psutil.cpu_percent()` ile anlık işlemci yükünü okur.
- `psutil.sensors_temperatures()` ile gerçek donanım sıcaklığını dener;
  platform desteklemiyorsa CPU yüküne dayalı gerçekçi simülasyon üretir.
- `psutil.cpu_freq()` ile anlık frekansı (MHz) alır.

### 2.3 GPUMonitor (BaseMonitor'dan türetildi)

- Opsiyonel `GPUtil` kütüphanesi kuruluysa gerçek GPU verisi alır.
- Kütüphane yoksa ya da hata oluşursa CPU yüküyle ilişkilendirilmiş, kayan
  pencereli dalgalanma algoritması ile gerçekçi simülasyon üretir.
- `_gpu_available` bayrağı ile iki mod (gerçek / simülasyon) şeffaf biçimde
  yönetilir; çağıran kod farkı görmez.

### 2.4 RAMMonitor (BaseMonitor'dan türetildi)

- `psutil.virtual_memory()` ile toplam, kullanılan ve boş RAM bilgisini alır.
- Değerleri GB cinsine dönüştürerek okunabilirlik sağlar.

### 2.5 FPSMonitor (BaseMonitor'dan türetildi)

- Gerçek oyun API erişimi olmadığından CPU yüküne ters orantılı, gürültülü bir
  simülasyon algoritması kullanır.
- `_frame_times` listesi son 60 kareyi tutar; bu liste üzerinden ortalama FPS
  ve anlık frame süresi (ms) hesaplanır.
- Temel FPS değeri (`_base_fps`) her adımda küçük rastgele değişimle güncellenir;
  bu sayede gerçekçi oyun davranışı taklit edilir.

### 2.6 DiskMonitor (BaseMonitor'dan türetildi)

- `psutil.disk_io_counters()` sayaçlarını ardışık iki çağrı arasındaki farkla
  bölerek anlık okuma/yazma hızını MB/s cinsinden hesaplar.
- `psutil.disk_usage("/")` ile disk doluluk yüzdesi ve boş alan (GB) alınır.

---

## 3. analyzer.py — Analiz ve Puanlama Modülü

### 3.1 PerformanceScore (Yardımcı Sınıf)

- **Sorumluluk:** Tek bir metrik değerini (0–100) puana ve metin etiketine çevirir.
- `reverse=True` parametresi ile yüksek değerin iyi olduğu metrikler (FPS) ters
  yönde puanlanır; böylece aynı sınıf tüm metrikler için yeniden kullanılır
  (*DRY* — Don't Repeat Yourself).
- Eşik değerleri (`low`, `mid`, `high`) nesne oluşturulurken belirlenir; bu da
  her metrik için farklı davranış sağlar (Kapsülleme).

### 3.2 SystemAnalyzer (Ana Analiz Sınıfı)

- `_scorers` sözlüğü sınıf değişkeni olarak tanımlanmıştır; tüm örnekler
  aynı eşik bilgisini paylaşır (bellek verimliliği).
- `evaluate(snapshot)` metodu:
  1. Her metrik için `PerformanceScore.score()` çağrılır.
  2. Metrik önem ağırlıklarıyla (FPS: 3.0, sıcaklıklar: 2.5, kullanım: 1.5…)
     ağırlıklı ortalama genel skor (0–100) hesaplanır.
  3. `_verdict()` statik metodu ile skora karşılık gelen metin kararı üretilir.
- `session_summary()` metodu oturum boyunca biriken tüm skorların
  min/max/ortalama istatistiklerini döndürür.

---

## 4. main.py — Arayüz ve Uygulama Modülü

### 4.1 GameMonitorApp (Ana GUI Sınıfı)

- `tkinter.Tk` nesnesini alır; tüm GUI durumu bu sınıfın içinde kapsüllenir.
- `_build_*` metodlarıyla arayüz bölümleri (başlık, kartlar, skor, tablo,
  kontroller) ayrı metodlara bölünmüştür; bu da bakım kolaylığı sağlar.
- `_loop()` metodu `threading.Thread(daemon=True)` ile arka planda çalışır;
  GUI dondurulmaz.
- `_root.after(0, callback)` çağrısı ile arka plan verileri ana GUI thread'ine
  güvenli biçimde aktarılır (tkinter thread-safety kuralına uyum).
- `COLORS` sözlüğü sınıf değişkeni olarak tanımlanmıştır; tema renkleri tek
  noktadan yönetilir.

---

## 5. OOP İlkelerinin Özet Tablosu

| OOP İlkesi | Nerede Kullanıldı | Örnek |
|---|---|---|
| **Sınıf (Class)** | Tüm modüller | `CPUMonitor`, `SystemAnalyzer`, `GameMonitorApp` |
| **Kalıtım (Inheritance)** | monitor.py | `CPUMonitor(BaseMonitor)`, `GPUMonitor(BaseMonitor)` |
| **Kapsülleme (Encapsulation)** | Tüm modüller | `_history`, `_name`, `_running` — korumalı alanlar |
| **Polimorfizm (Polymorphism)** | monitor.py | `collect()` her alt sınıfta farklı davranır |
| **Soyutlama (Abstraction)** | BaseMonitor | `collect()` `NotImplementedError` ile soyutlanır |
| **Property (Getter)** | BaseMonitor | `@property name`, `@property history` |
| **Statik Metod** | analyzer.py | `@staticmethod _verdict()` |
| **Sınıf Değişkeni** | analyzer.py | `_scorers` tüm örneklerce paylaşılır |
