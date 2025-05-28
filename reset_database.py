import psycopg2

def reset_database():
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

        # Tabloları silme
        cur.execute("""
            DROP TABLE IF EXISTS uyarilar CASCADE;
            DROP TABLE IF EXISTS hasta_belirtileri CASCADE;
            DROP TABLE IF EXISTS belirtiler CASCADE;
            DROP TABLE IF EXISTS diyet_kayitlari CASCADE;
            DROP TABLE IF EXISTS egzersiz_kayitlari CASCADE;
            DROP TABLE IF EXISTS kan_sekeri_olcumleri CASCADE;
            DROP TABLE IF EXISTS doktor_hasta_iliskisi CASCADE;
            DROP TABLE IF EXISTS kullanicilar CASCADE;
        """)

        # Değişiklikleri kaydet
        conn.commit()
        print("Tüm tablolar başarıyla silindi!")

    except Exception as e:
        print("Hata oluştu:", e)
        conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    reset_database() 