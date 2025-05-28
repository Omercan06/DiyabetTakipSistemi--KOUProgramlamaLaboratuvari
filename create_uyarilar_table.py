import psycopg2

try:
    conn = psycopg2.connect(
        dbname="diyabet_takip",
        user="postgres",
        password="1",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()
    # Eğer tablo varsa sil ve yeniden oluştur
    cur.execute("""
        DROP TABLE IF EXISTS uyarilar;
        CREATE TABLE uyarilar (
            uyari_id SERIAL PRIMARY KEY,
            hasta_id INTEGER REFERENCES kullanicilar(kullanici_id),
            uyari_zamani TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            uyari_tipi VARCHAR(100),
            uyari_mesaji TEXT
        );
    """)
    conn.commit()
    print("uyarilar tablosu başarıyla oluşturuldu!")
except Exception as e:
    print("Hata oluştu:", e)
finally:
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close()