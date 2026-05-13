# analyzer.py - Toplanan verileri analiz eden ve değerlendiren sınıflar

# ───────────────────────────────────────────────
# PERFORMANS SKORU SINIFI
# ───────────────────────────────────────────────
class PerformanceScore:
    """Tek bir metriği eşik değerleriyle puanlar (0-100)."""

    def __init__(self, name: str, low: float, mid: float, high: float, reverse=False):
        self._name    = name     # Metrik adı (örn. "CPU Sıcaklık")
        self._low     = low      # İyi/orta sınırı
        self._mid     = mid      # Orta/kötü sınırı
        self._high    = high     # Kritik sınır
        self._reverse = reverse  # True ise yüksek değer iyidir (FPS gibi)

    def score(self, value: float) -> int:
        """Değeri 0-100 arası puana çevirir."""
        if self._reverse:                       # Yüksek değer iyiyse (FPS)
            if   value >= self._high: return 100
            elif value >= self._mid : return 70
            elif value >= self._low : return 40
            else                    : return 10
        else:                                   # Düşük değer iyiyse (sıcaklık, kullanım)
            if   value <= self._low : return 100
            elif value <= self._mid : return 70
            elif value <= self._high: return 40
            else                    : return 10

    def label(self, value: float) -> str:
        """Puana karşılık gelen metin etiketini döndürür."""
        s = self.score(value)
        if s >= 85 : return "Mükemmel"   # En iyi durum
        if s >= 65 : return "İyi"        # Kabul edilebilir
        if s >= 35 : return "Orta"       # Dikkat edilmeli
        return          "Kritik"         # Acil müdahale gerekli


# ───────────────────────────────────────────────
# ANA ANALİZÖR SINIFI
# ───────────────────────────────────────────────
class SystemAnalyzer:
    """Tüm monitörlerden gelen ortalama verileri birleştirip genel skor üretir."""

    # Skor hesaplayıcıları sınıf değişkeni olarak tanımla (tüm örnekler paylaşır)
    _scorers = {
        "cpu_usage"      : PerformanceScore("CPU Kullanım"   ,  50,  75,  90),
        "cpu_temp"       : PerformanceScore("CPU Sıcaklık"   ,  65,  80,  90),
        "gpu_usage"      : PerformanceScore("GPU Kullanım"   ,  60,  80,  95),
        "gpu_temp"       : PerformanceScore("GPU Sıcaklık"   ,  70,  83,  90),
        "ram_usage"      : PerformanceScore("RAM Kullanım"   ,  60,  80,  90),
        "fps"            : PerformanceScore("FPS"            ,  30,  60,  90, reverse=True),
        "disk_usage"     : PerformanceScore("Disk Doluluk"   ,  70,  85,  95),
    }

    def __init__(self):
        self._session_scores = []   # Oturumun her anına ait skor listesi

    def evaluate(self, snapshot: dict) -> dict:
        """
        Anlık veri sözlüğünü alır; her metrik için puan hesaplar,
        ağırlıklı genel skoru bulur ve sonuç sözlüğü döndürür.
        """
        results  = {}   # Metrik bazlı sonuçlar
        scores   = []   # Ağırlıklı ortalama için puan listesi
        weights  = []   # Her metriğin ağırlığı

        # Metrik → snapshot anahtarı ve ağırlık eşlemeleri
        mapping = {
            "fps"        : ("fps"        , 3.0),  # FPS en kritik oyun metriği
            "cpu_temp"   : ("cpu_temp"   , 2.5),  # Sıcaklık aşımı donanıma zarar verir
            "gpu_temp"   : ("gpu_temp"   , 2.5),
            "cpu_usage"  : ("cpu_usage"  , 1.5),
            "gpu_usage"  : ("gpu_usage"  , 1.5),
            "ram_usage"  : ("ram_usage"  , 1.0),
            "disk_usage" : ("disk_usage" , 0.5),
        }

        for metric, (key, weight) in mapping.items():
            value = snapshot.get(key, None)        # Anlık değeri al
            if value is None:
                continue                           # Eksik veri varsa atla
            scorer = self._scorers[metric]         # İlgili skor hesaplayıcı
            s      = scorer.score(value)           # Ham puan
            lbl    = scorer.label(value)           # Metin etiketi
            results[metric] = {"value": value, "score": s, "label": lbl}
            scores.append(s * weight)              # Ağırlıklı puan ekle
            weights.append(weight)                 # Ağırlığı kaydet

        # Ağırlıklı genel skor
        overall = round(sum(scores) / sum(weights), 1) if weights else 0
        self._session_scores.append(overall)       # Oturum geçmişine ekle

        return {
            "metrics" : results,                   # Metrik detayları
            "overall" : overall,                   # Genel skor (0-100)
            "verdict" : self._verdict(overall),    # Metin yargısı
        }

    @staticmethod
    def _verdict(score: float) -> str:
        """Genel skora göre oyunculuğa uygunluk kararı verir."""
        if score >= 85: return "🟢 Sistem Oyun İçin Hazır"
        if score >= 65: return "🟡 Performans Kabul Edilebilir"
        if score >= 40: return "🟠 Optimizasyon Önerilir"
        return              "🔴 Kritik — Oyunu Durdur"

    def session_average(self) -> float:
        """Oturum boyunca oluşan tüm anlık skorların ortalaması."""
        if not self._session_scores:
            return 0.0
        return round(sum(self._session_scores) / len(self._session_scores), 1)

    def session_summary(self) -> dict:
        """Oturum sonunda özet istatistikleri döndürür."""
        if not self._session_scores:
            return {}
        return {
            "avg_score" : self.session_average(),
            "min_score" : min(self._session_scores),  # En düşük skor anı
            "max_score" : max(self._session_scores),  # En yüksek skor anı
            "samples"   : len(self._session_scores),  # Toplam ölçüm sayısı
            "verdict"   : self._verdict(self.session_average()),
        }
