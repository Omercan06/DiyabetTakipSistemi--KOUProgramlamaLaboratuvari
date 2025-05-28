import psycopg2
from datetime import datetime, date
import hashlib

def hash_password(password):
    """Şifreyi hash'ler"""
    return hashlib.sha256(password.encode()).hexdigest()

def insert_sample_data():
    try:
        # Veritabanı bağlantısı
        conn = psycopg2.connect(
            dbname="diyabet_takip",
            user="postgres",
            password="1",  # PostgreSQL şifreniz
            host="localhost",
            port="5432"
        )
        cur = conn.cursor()

        # Örnek doktor ekleme
        cur.execute("""
            INSERT INTO kullanicilar (tc_kimlik, ad, soyad, email, sifre, dogum_tarihi, cinsiyet, kullanici_tipi)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING kullanici_id
        """, (
            '12345678901',
            'Ahmet',
            'Yılmaz',
            'ahmet.yilmaz@hastane.com',
            hash_password('doktor123'),
            date(1980, 1, 1),
            'E',
            'DOKTOR'
        ))
        doktor_id = cur.fetchone()[0]

        # Örnek hasta ekleme
        cur.execute("""
            INSERT INTO kullanicilar (tc_kimlik, ad, soyad, email, sifre, dogum_tarihi, cinsiyet, kullanici_tipi)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING kullanici_id
        """, (
            '98765432109',
            'Ayşe',
            'Demir',
            'ayse.demir@email.com',
            hash_password('hasta123'),
            date(1990, 5, 15),
            'K',
            'HASTA'
        ))
        hasta_id = cur.fetchone()[0]

        # Doktor-Hasta ilişkisi
        cur.execute("""
            INSERT INTO doktor_hasta_iliskisi (doktor_id, hasta_id)
            VALUES (%s, %s)
        """, (doktor_id, hasta_id))

        # Örnek kan şekeri ölçümleri
        olcum_tipleri = ['SABAH', 'OGLEN', 'IKINDI', 'AKSAM', 'GECE']
        for i, tip in enumerate(olcum_tipleri):
            cur.execute("""
                INSERT INTO kan_sekeri_olcumleri (hasta_id, olcum_degeri, olcum_zamani, olcum_tipi)
                VALUES (%s, %s, %s, %s)
            """, (
                hasta_id,
                100 + i * 10,  # Örnek değerler
                datetime.now(),
                tip
            ))

        # Örnek egzersiz kaydı
        cur.execute("""
            INSERT INTO egzersiz_kayitlari (hasta_id, egzersiz_tipi, yapildi, kayit_tarihi)
            VALUES (%s, %s, %s, %s)
        """, (
            hasta_id,
            'YURUYUS',
            True,
            date.today()
        ))

        # Örnek diyet kaydı
        cur.execute("""
            INSERT INTO diyet_kayitlari (hasta_id, diyet_tipi, uygulandi, kayit_tarihi)
            VALUES (%s, %s, %s, %s)
        """, (
            hasta_id,
            'AZ_SEKERLI',
            True,
            date.today()
        ))

        # Örnek belirti kaydı
        cur.execute("""
            INSERT INTO hasta_belirtileri (hasta_id, belirti_id, kayit_tarihi)
            VALUES (%s, %s, %s)
        """, (
            hasta_id,
            1,  # Poliüri belirtisi
            date.today()
        ))

        # Örnek uyarı
        cur.execute("""
            INSERT INTO uyarilar (hasta_id, uyari_tipi, uyari_mesaji, uyari_tarihi)
            VALUES (%s, %s, %s, %s)
        """, (
            hasta_id,
            'KAN_SEKERI_YUKSEK',
            'Kan şekeri seviyeniz yüksek. Lütfen doktorunuza danışın.',
            datetime.now()
        ))

        # Değişiklikleri kaydet
        conn.commit()
        print("Örnek veriler başarıyla eklendi!")

    except Exception as e:
        print("Hata oluştu:", e)
        conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    insert_sample_data() 