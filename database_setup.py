import psycopg2
from psycopg2 import sql

def create_tables():
    try:
        # Veritabanı bağlantısı
        conn = psycopg2.connect(
            dbname="diyabet_takip",
            user="postgres",
            password="1",  # PostgreSQL kurulumunda belirlediğiniz şifre
            host="localhost",
            port="5432"
        )
        cur = conn.cursor()

        # Kullanıcılar tablosu
        cur.execute("""
            CREATE TABLE IF NOT EXISTS kullanicilar (
                kullanici_id SERIAL PRIMARY KEY,
                tc_kimlik VARCHAR(11) UNIQUE NOT NULL,
                ad VARCHAR(50) NOT NULL,
                soyad VARCHAR(50) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                sifre VARCHAR(255) NOT NULL,
                dogum_tarihi DATE NOT NULL,
                cinsiyet CHAR(1) CHECK (cinsiyet IN ('E', 'K')),
                profil_resmi BYTEA,
                kullanici_tipi VARCHAR(10) CHECK (kullanici_tipi IN ('DOKTOR', 'HASTA')),
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Doktor-Hasta İlişki tablosu
        cur.execute("""
            CREATE TABLE IF NOT EXISTS doktor_hasta_iliskisi (
                iliski_id SERIAL PRIMARY KEY,
                doktor_id INTEGER REFERENCES kullanicilar(kullanici_id),
                hasta_id INTEGER REFERENCES kullanicilar(kullanici_id),
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(doktor_id, hasta_id)
            );
        """)

        # Kan Şekeri Ölçümleri tablosu
        cur.execute("""
            CREATE TABLE IF NOT EXISTS kan_sekeri_olcumleri (
                olcum_id SERIAL PRIMARY KEY,
                hasta_id INTEGER REFERENCES kullanicilar(kullanici_id),
                olcum_degeri INTEGER NOT NULL,
                olcum_zamani TIMESTAMP NOT NULL,
                olcum_tipi VARCHAR(20) CHECK (olcum_tipi IN ('SABAH', 'OGLEN', 'IKINDI', 'AKSAM', 'GECE')),
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Egzersiz Kayıtları tablosu
        cur.execute("""
            CREATE TABLE IF NOT EXISTS egzersiz_kayitlari (
                kayit_id SERIAL PRIMARY KEY,
                hasta_id INTEGER REFERENCES kullanicilar(kullanici_id),
                egzersiz_tipi VARCHAR(50) CHECK (egzersiz_tipi IN ('YURUYUS', 'BISIKLET', 'KLINIK')),
                yapildi BOOLEAN DEFAULT FALSE,
                kayit_tarihi DATE NOT NULL,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Diyet Kayıtları tablosu
        cur.execute("""
            CREATE TABLE IF NOT EXISTS diyet_kayitlari (
                kayit_id SERIAL PRIMARY KEY,
                hasta_id INTEGER REFERENCES kullanicilar(kullanici_id),
                diyet_tipi VARCHAR(50) CHECK (diyet_tipi IN ('AZ_SEKERLI', 'SEKERSIZ', 'DENGELI')),
                uygulandi BOOLEAN DEFAULT FALSE,
                kayit_tarihi DATE NOT NULL,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Belirtiler tablosu
        cur.execute("""
            CREATE TABLE IF NOT EXISTS belirtiler (
                belirti_id SERIAL PRIMARY KEY,
                belirti_adi VARCHAR(100) UNIQUE NOT NULL
            );
        """)

        # Hasta Belirtileri tablosu
        cur.execute("""
            CREATE TABLE IF NOT EXISTS hasta_belirtileri (
                kayit_id SERIAL PRIMARY KEY,
                hasta_id INTEGER REFERENCES kullanicilar(kullanici_id),
                belirti_id INTEGER REFERENCES belirtiler(belirti_id),
                kayit_tarihi DATE NOT NULL,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Uyarılar tablosu
        cur.execute("""
            CREATE TABLE IF NOT EXISTS uyarilar (
                uyari_id SERIAL PRIMARY KEY,
                hasta_id INTEGER REFERENCES kullanicilar(kullanici_id),
                uyari_tipi VARCHAR(50) NOT NULL,
                uyari_mesaji TEXT NOT NULL,
                uyari_tarihi TIMESTAMP NOT NULL,
                okundu BOOLEAN DEFAULT FALSE,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Belirtileri ekle
        cur.execute("""
            INSERT INTO belirtiler (belirti_adi) VALUES
            ('Poliüri'),
            ('Polifaji'),
            ('Polidipsi'),
            ('Nöropati'),
            ('Kilo kaybı'),
            ('Yorgunluk'),
            ('Yaraların yavaş iyileşmesi'),
            ('Bulanık görme')
            ON CONFLICT (belirti_adi) DO NOTHING;
        """)

        # Değişiklikleri kaydet
        conn.commit()
        print("Tüm tablolar başarıyla oluşturuldu!")

    except Exception as e:
        print("Hata oluştu:", e)
        conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    create_tables() 