# 🩸 Diyabet Takip Sistemi (Diabetes Tracking System)

Bu proje, hastaların diyabet süreçlerini günlük olarak takip etmelerini ve doktorların kendilerine bağlı hastaları uzaktan, anlık verilerle izleyebilmelerini sağlayan kapsamlı bir masaüstü sağlık uygulamasıdır. Python ve PyQt6 kullanılarak modern bir arayüzle geliştirilmiş olup, verilerin güvenli ve düzenli saklanması için güçlü bir ilişkisel veritabanı olan PostgreSQL kullanmaktadır. 

Şifreler veritabanında SHA-256 algoritması ile şifrelenerek güvenli bir şekilde saklanmaktadır.

## 🚀 Temel Özellikler

Sistem **Doktor** ve **Hasta** olmak üzere iki farklı role sahip kullanıcılar için özel paneller sunar.

### 👨‍⚕️ Doktor Paneli (`doctor_panel.py`)
* **Hasta Yönetimi:** Kayıtlı hastaları listeleme, sisteme yeni hasta ekleme veya silme işlemleri.
* **Gelişmiş Filtreleme:** Hastaları belirli kan şekeri aralıklarına veya yaşanılan spesifik belirtilere göre filtreleme.
* **Akıllı Öneri ve Uyarı Sistemi:** Hastanın ölçüm değerlerine ve yaşadığı belirtilere (Örn: Bulanık görme, Nöropati vb.) bakarak otomatik olarak Az Şekerli/Şekersiz diyetler ve İnsülin doz önerisi (1 ml, 2 ml vb.) hesaplama.
* **Kan Şekeri Analizi:** Hastaların geçmiş ölçümlerini, uyguladıkları diyetleri ve yaptıkları egzersizleri Matplotlib grafikleri üzerinden tarih aralığı bazlı analiz etme.
* **Manuel Uyarılar:** Eksik veya tehlikeli ölçüm yapan hastaların panellerine "Hiperglisemi Riski", "Ölçüm Eksik" gibi manuel uyarılar gönderebilme.

### 🤒 Hasta Paneli (`patient_panel.py`)
* **Ölçüm Girişleri:** Günün belirli periyotlarında (Sabah, Öğlen, İkindi, Akşam, Gece) detaylı kan şekeri değerlerini sisteme kaydetme.
* **Egzersiz ve Diyet Takibi:** Diyet tiplerini (Dengeli, Az Şekerli vb.) ve egzersiz türlerini (Yürüyüş, Bisiklet vb.) sisteme ekleme ve günlük uygulama oranlarını bir progress bar üzerinden yüzdesel olarak takip etme.
* **Belirti Bildirimi:** Yaşanılan yan etkileri ve diyabet semptomlarını (Poliüri, Polifaji, Yorgunluk vb.) anlık olarak sisteme kaydedip doktorun görüşüne sunma.
* **Kişisel Analiz:** Kendi kan şekeri seyirlerini grafikler yardımıyla görebilme.

## 🛠️ Kullanılan Teknolojiler

* **Programlama Dili:** Python 3.x
* **GUI (Arayüz):** PyQt6
* **Veritabanı:** PostgreSQL (psycopg2-binary adaptörü ile)
* **Veri Görselleştirme:** Matplotlib & NumPy
* **Güvenlik:** Hashlib (SHA-256 Şifreleme)

## 📁 Proje Dosya Yapısı
* `login.py`: Sisteme giriş ekranı.
* `doctor_panel.py`: Doktorlar için tasarlanmış geniş kapsamlı arayüz.
* `patient_panel.py`: Hastaların kendi süreçlerini yönetebildiği arayüz.
* `database_setup.py`: Sistem için gereken tüm tabloların ve ilişkilerin (kullanicilar, doktor_hasta_iliskisi vb.) oluşturulması.
* `sample_data.py`: Sistemi test etmek için örnek hastalar, belirtiler, diyet kayıtları ve ölçümler oluşturur.
* `reset_database.py` / `create_uyarilar_table.py`: Veritabanını sıfırlamak ve bakım yapmak için yardımcı araçlar.
* `requirements.txt`: Sistemin çalışması için gerekli kütüphanelerin listesi.

## 💻 Kurulum ve Çalıştırma

Projeyi yerel bilgisayarınızda çalıştırmak için aşağıdaki adımları sırasıyla uygulayın:

**1. Veritabanı Hazırlığı:**
Öncelikle bilgisayarınızda **PostgreSQL** kurulu olmalıdır. 
Arayüzden (pgAdmin vs.) veya komut satırından `diyabet_takip` adında boş bir veritabanı oluşturun.
> **Not:** Kod dosyalarındaki (`database_setup.py`, `login.py`, `patient_panel.py` vb.) `password="1"` kısımlarını kendi PostgreSQL şifrenizle değiştirmeyi unutmayın!

**2. Repoyu Klonlayın ve Gerekli Kütüphaneleri Yükleyin:**
```bash
git clone <repo_url>
cd <repo_klasor_adi>
pip install -r requirements.txt
