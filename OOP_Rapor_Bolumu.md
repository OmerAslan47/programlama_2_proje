# TEKNİK RAPOR — OOP YAPISI VE MODÜLLERİN AÇIKLAMASI

**Proje Adı:** GameSpy Monitor – Oyun Performans İzleme Aracı  
**Kastamonu Üniversitesi Tosya Meslek Yüksekokulu | Programlama II**

---

## 1. Genel Mimari Bakış

Proje üç Python modülüne bölünmüştür:

- **`monitor.py`** – Ham veri toplayan sensör sınıfları  
- **`analyzer.py`** – Verileri yorumlayan ve puanlayan analiz sınıfları  
- **`main.py`** – Grafik arayüzü ve uygulama akışını yöneten ana dosya

Bu ayrım, her modülün tek bir sorumluluğa (Single Responsibility) sahip olmasını sağlar ve kodun bakımını, test edilmesini kolaylaştırır.

---

## 2. Modül 1: monitor.py — Sensör Katmanı

### 2.1 SensorBase (Temel Sınıf)

**Tür:** Soyut Temel Sınıf (Abstract Base)  
**Amaç:** Tüm sensör sınıflarının ortak davranışlarını ve sözleşmesini tanımlar.

**Öne Çıkan OOP Unsurları:**

- **Kapsülleme:** `_name`, `_readings`, `_last_value` gibi tüm özellikler tek alt çizgi (`_`) ile koruma altına alınmıştır. Dışarıdan erişim yalnızca `@property` dekoratörleriyle sağlanır.
- **Soyutlama:** `read()` ve `score()` metotları `raise NotImplementedError` ile işaretlenmiştir; bu, Python'da sözleşme tanımlamanın yaygın yoludur.
- **Bellek Yönetimi:** `_save_reading()` metodu, listeyi maksimum 1000 kayıtla sınırlayarak bellek taşmasını engeller.

**Sağladığı Metotlar:** `read()`, `get_average()`, `get_max()`, `get_min()`, `reset()`, `_save_reading()`

---

### 2.2 FPSSensor (SensorBase → Kalıtım)

**Tür:** Somut Sınıf  
**Amaç:** Kare/saniye değerini simüle eder veya ölçer.

**OOP Unsurları:**

- **Kalıtım:** `SensorBase.__init__()` çağrısı `super().__init__()` ile yapılır; üst sınıfın tüm özellik ve metotları miras alınır.
- **Property + Setter:** `target_fps` özelliği hem okunabilir hem de doğrulamalı olarak yazılabilirdir (1–360 aralığı kontrolü).
- **Özel Davranış:** `get_stability_score()` sadece FPS'e özgü bir metottur; üst sınıfta bulunmaz. Bu, kalıtımla davranış genişletmeye örnektir.

---

### 2.3 CPUTemperatureSensor (SensorBase → Kalıtım)

**Tür:** Somut Sınıf  
**Amaç:** CPU sıcaklığını gerçek `psutil` kütüphanesi üzerinden veya simülasyonla okur.

**OOP Unsurları:**

- **Kapsülleme:** `_warning_threshold` ve `_critical_threshold` dışarıdan doğrudan değiştirilemez; yalnızca `get_status()` metodu bu değerleri kullanır.
- **Çalışma Zamanı Polimorfizmi:** `read()` metodu mevcut ortama (psutil var mı?) göre farklı dallar izler. Dışarıdan bakıldığında yalnızca `sensor.read()` çağrısı yapılır; içeride ne olduğu gizlidir.

---

### 2.4 GPUTemperatureSensor (CPUTemperatureSensor → Kalıtım)

**Tür:** Somut Sınıf (İki Katmanlı Kalıtım)  
**Amaç:** GPU'ya özgü sıcaklık davranışını modellemek için CPU sensöründen türetilmiştir.

**OOP Unsurları:**

- **Çok Katmanlı Kalıtım:** `SensorBase → CPUTemperatureSensor → GPUTemperatureSensor` zinciri oluşturulmuştur. `GPUTemperatureSensor`, `CPUTemperatureSensor`'ın tüm özelliklerini alır ve yalnızca GPU'ya özgü eşik değerlerini (83°C / 92°C) ve VRAM yük faktörünü (`_vram_load`) ekler.
- **Method Overriding:** `read()` metodu GPU'nun ısı modelini yansıtacak şekilde yeniden yazılmıştır.
- **Kod Tekrarının Önlenmesi (DRY):** CPU sıcaklık mantığının büyük bölümü üst sınıftan miras alınarak tekrardan kaçınılmıştır.

---

### 2.5 Diğer Sensörler

Aynı `SensorBase` kalıtım zincirini izleyen:

| Sınıf | Ölçüm | Özel Davranış |
|---|---|---|
| `CPUUsageSensor` | CPU % kullanımı | `set_game_boost()` ile yük simülasyonu |
| `RAMUsageSensor` | RAM % kullanımı | `get_used_gb()` ve `get_total_gb()` ek metotları |
| `DiskUsageSensor` | Disk doluluk | `get_io_activity()` ayrı I/O verisi |
| `NetworkSensor` | Ağ hızı (Mbps) | Delta hesabıyla anlık hız |
| `BatterySensor` | Pil % ve şarj durumu | `is_charging()` boolean metodu |

---

### 2.6 GameProfileManager

**Tür:** Bağımsız Sınıf (Inheritance yok)  
**Amaç:** Farklı oyun senaryolarını (hafif/orta/ağır/stres) sensör yük değerleri olarak tanımlar ve uygular.

**OOP Unsurları:**

- **Sınıf Değişkeni:** `PROFILES` sözlüğü `class` kapsamında tanımlanmıştır; tüm nesneler aynı profil verisini paylaşır (bellek tasarrufu).
- **Bağımlılık Enjeksiyonu:** `apply_profile()` metodu bir `SensorGroup` nesnesi alarak sensörlere yük değerlerini dışarıdan uygular; bu sayede `GameProfileManager` ile sensörler birbirine sıkı bağlı değildir (loose coupling).
- **@staticmethod:** `list_profiles()`, nesne durumuna bağlı olmadığından statik metot olarak tanımlanmıştır.

---

### 2.7 SensorGroup

**Tür:** Konteyner Sınıf (Composition – Bileşim)  
**Amaç:** Tüm sensör nesnelerini tek bir çatı altında toplar.

**OOP Unsurları:**

- **Composition:** Kalıtım yerine bileşim tercih edilmiştir. `SensorGroup`, her sensörü bir özellik olarak barındırır (`self.fps_sensor = FPSSensor()` vb.).
- **Toplu İşlem:** `_all_sensors` listesi, `reset_all()` gibi toplu işlemleri döngüyle gerçekleştirir.
- **Veri Toplaması:** `read_all()` tüm sensörleri çağırıp tek bir sözlük döndürür; dışarıdan tek bir metot çağrısı yeterlidir.

---

## 3. Modül 2: analyzer.py — Analiz Katmanı

### 3.1 AnalyzerBase (Temel Sınıf)

**Tür:** Soyut Temel Sınıf  
**Amaç:** Tüm analizör sınıflarının `analyze()` ve `score()` sözleşmesine uymasını zorunlu kılar.

**OOP Unsurları:**

- **Polimorfizm Sözleşmesi:** Her alt sınıf `analyze()` ve `score()` metodunu farklı biçimde uygular; ancak dışarıdan bakıldığında aynı arayüz kullanılır.
- **@staticmethod Yardımcı Metot:** `_clamp()` sınıfın tüm alt örneklerince kullanılacak saf bir yardımcı işlevdir.

---

### 3.2 FPSAnalyzer (AnalyzerBase → Kalıtım)

**Tür:** Somut Sınıf  
**Amaç:** FPS değerini hedef FPS'e oranla kategorize eder ve puanlar.

**OOP Unsurları:**

- Hedef FPS constructor'dan alınır; sınıf bu değerle örneklenir (parametre ile özelleştirme).
- `check_stutter()` FPS listesinde 20'den fazla ani düşüş arayan ek bir davranıştır; polimorfik arayüzü genişletir.

---

### 3.3 TemperatureAnalyzer (AnalyzerBase → Kalıtım)

**Tür:** Somut Sınıf  
**Amaç:** Hem CPU hem GPU sıcaklıklarını tek sınıfla farklı eşik değerleri kullanarak değerlendirir.

**OOP Unsurları:**

- **Constructor Parametresiyle Davranış Farkı:** `component="GPU"` parametresi verilirse eşik değerleri GPU normlarına ayarlanır. Aynı sınıf, farklı örneklerle farklı davranır (parametrik polimorfizm).
- **Lineer İnterpolasyon:** `score()` iyi ile kritik eşikler arasında sürekli bir puan üretir; yalnızca iki noktadan oluşan kaba bir derecelendirme yerine daha adil bir değerlendirme sağlar.

---

### 3.4 UsageAnalyzer (AnalyzerBase → Kalıtım)

**Tür:** Somut Sınıf  
**Amaç:** CPU, RAM ve disk gibi yüzde bazlı kullanım değerleri için genel analizör.

**OOP Unsurları:**

- **`invert_score` Bayrağı:** Kural olarak düşük kullanım = yüksek puan olduğundan `invert_score=True` varsayılandır. Ağ hızı için `False` geçirilir (yüksek hız = yüksek puan). Bu, sınıfın tek yapıyla birden fazla senaryoya uyum sağlamasını gösterir.

---

### 3.5 SystemEvaluator

**Tür:** Bileşik Sınıf (Tüm analizörleri içerir – Composition)  
**Amaç:** Anlık ölçümü 7 ayrı analizörden geçirir, ağırlıklı toplam puan üretir, oturum istatistiklerini biriktirir.

**OOP Unsurları:**

- **Ağırlık Sözlüğü (`WEIGHTS`):** Sınıf içinde tanımlanmış ve merkezi olarak yönetilir; bir metriğin ağırlığını değiştirmek için tek bir yeri güncellemek yeterlidir.
- **Oturum Durumu:** `_session_scores` ve `_session_data` listelerinde oturum boyunca veri biriktirilir. Bu, nesnenin durumunu (state) sakladığının göstergesidir.
- **`_grade()` Yardımcı Metodu:** Puana göre harf notu atayan bu metot kasıtlı olarak `private` (tek alt çizgi) yapılmıştır; dışarıdan çağrılmaması gerekir.

---

### 3.6 AlertManager (AnalyzerBase → Kalıtım)

**Tür:** Somut Sınıf  
**Amaç:** Her ölçüm döngüsünde eşik değerlerini kontrol eder, uyarı üretir ve geçmişe kaydeder.

**OOP Unsurları:**

- **Kapsülleme:** `_thresholds` sözlüğü özel tutulur; eşikler nesne içinden kontrol edilir.
- **Durum Takibi:** `_active_alerts` (anlık) ve `_alert_history` (kalıcı) iki ayrı liste; bu ayrım yönetim kolaylığı sağlar.

---

### 3.7 ReportGenerator (AnalyzerBase → Kalıtım)

**Tür:** Somut Sınıf  
**Amaç:** Oturum istatistiklerinden metin ve JSON rapor üretir.

**OOP Unsurları:**

- Raporlama sorumluluğu ayrı bir sınıfa taşınmıştır (tek sorumluluk ilkesi).
- `generate_text_report()` ve `save_json_report()` iki farklı çıktı biçimini destekler; ilerde HTML rapor eklemek için yeni bir metot eklenmesi yeterlidir.

---

## 4. Modül 3: main.py — Sunum Katmanı

### 4.1 ColorPalette

- Tüm renk sabitleri merkezi bir sınıfta toplanmıştır. Tema değişikliği tek noktadan yapılabilir.
- İçeriği salt okunurdur; sınıf örneklenmez (sabit deposu görevi).

### 4.2 MetricCard

- Tek bir metriği görselleştiren yeniden kullanılabilir bileşen.
- `update()` metodu değeri, rengi ve alt metni bir arada günceller; dışarıdan ayrıntılar gizlidir (kapsülleme).

### 4.3 MiniChart

- Canvas üzerinde kaydırmalı çizgi grafik çizer.
- `_history` listesi en fazla 60 eleman tutar; sınır aşılınca en eski değer silinir.

### 4.4 AlertPanel

- `Text` widget'ı üzerine renkli uyarı satırları yazar.
- `update_alerts()` metodu çağrılana kadar widget kilitlidir (salt okunur).

### 4.5 GameMonitorApp (Ana Uygulama)

- Tüm bileşenleri oluşturur ve yaşam döngüsünü yönetir.
- **Threading:** `_monitor_loop()` ayrı bir `daemon` iş parçacığında çalışır; GUI donmaz.
- **`root.after(0, ...)`:** Tkinter'ın `after` mekanizması, arka planından GUI'ye güvenli veri geçişini sağlar.
- Kapatma olayı override edilmiş (`_on_close`); aktif izleme varsa kullanıcıya onay sorulur.

---

## 5. Kalıtım Ağacı (Özet)

```
object
├── SensorBase
│   ├── FPSSensor
│   ├── CPUTemperatureSensor
│   │   └── GPUTemperatureSensor
│   ├── CPUUsageSensor
│   ├── RAMUsageSensor
│   ├── DiskUsageSensor
│   ├── NetworkSensor
│   └── BatterySensor
│
├── AnalyzerBase
│   ├── FPSAnalyzer
│   ├── TemperatureAnalyzer
│   ├── UsageAnalyzer
│   ├── AlertManager
│   └── ReportGenerator
│
├── GameProfileManager   (bağımsız)
├── SensorGroup          (composition – SensorBase nesnelerini içerir)
├── SystemEvaluator      (composition – AnalyzerBase nesnelerini içerir)
│
└── GameMonitorApp       (composition – hepsini bir araya getirir)
```

---

## 6. Uygulanan OOP Prensipleri — Özet Tablo

| Prensip | Nerede Kullanıldı |
|---|---|
| **Kalıtım** | `GPUTemperatureSensor → CPUTemperatureSensor → SensorBase` gibi tüm sensör/analizör zincirleri |
| **Kapsülleme** | `_name`, `_readings`, `_thresholds` gibi tek alt çizgi ile korunan tüm özellikler |
| **Soyutlama** | `SensorBase.read()` ve `AnalyzerBase.analyze()` — `NotImplementedError` ile zorunlu kılınan metodlar |
| **Polimorfizm** | Aynı `read()` çağrısıyla her sensörün farklı davranması; `TemperatureAnalyzer`'ın CPU/GPU için farklı eşikler kullanması |
| **Composition** | `SensorGroup` (sensörleri içerir), `SystemEvaluator` (analizörleri içerir), `GameMonitorApp` (hepsini içerir) |
| **Single Responsibility** | Her sınıfın tek bir görevi: sensörler veri toplar, analizörler puanlar, uygulama görselleştirir |
| **DRY (Tekrar Etme)** | Ortak kayıt, ortalama, min/max mantığı `SensorBase`'de bir kez yazılmıştır |
