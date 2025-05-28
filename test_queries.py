import psycopg2
from tabulate import tabulate

def test_queries():
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

        print("\n1. Kullanıcılar Tablosu:")
        cur.execute("""
            SELECT kullanici_id, tc_kimlik, ad, soyad, email, kullanici_tipi 
            FROM kullanicilar
        """)
        print(tabulate(cur.fetchall(), 
                      headers=['ID', 'TC', 'Ad', 'Soyad', 'Email', 'Kullanıcı Tipi'],
                      tablefmt='grid'))

        print("\n2. Doktor-Hasta İlişkileri:")
        cur.execute("""
            SELECT 
                d.tc_kimlik as doktor_tc,
                d.ad as doktor_ad,
                d.soyad as doktor_soyad,
                h.tc_kimlik as hasta_tc,
                h.ad as hasta_ad,
                h.soyad as hasta_soyad
            FROM doktor_hasta_iliskisi di
            JOIN kullanicilar d ON di.doktor_id = d.kullanici_id
            JOIN kullanicilar h ON di.hasta_id = h.kullanici_id
        """)
        print(tabulate(cur.fetchall(), 
                      headers=['Doktor TC', 'Doktor Ad', 'Doktor Soyad', 
                              'Hasta TC', 'Hasta Ad', 'Hasta Soyad'],
                      tablefmt='grid'))

        print("\n3. Kan Şekeri Ölçümleri:")
        cur.execute("""
            SELECT 
                k.ad as hasta_ad,
                k.soyad as hasta_soyad,
                ko.olcum_degeri,
                ko.olcum_tipi,
                ko.olcum_zamani
            FROM kan_sekeri_olcumleri ko
            JOIN kullanicilar k ON ko.hasta_id = k.kullanici_id
            ORDER BY ko.olcum_zamani DESC
        """)
        print(tabulate(cur.fetchall(), 
                      headers=['Hasta Ad', 'Hasta Soyad', 'Ölçüm Değeri', 
                              'Ölçüm Tipi', 'Ölçüm Zamanı'],
                      tablefmt='grid'))

        print("\n4. Egzersiz ve Diyet Kayıtları:")
        cur.execute("""
            SELECT 
                k.ad as hasta_ad,
                k.soyad as hasta_soyad,
                ek.egzersiz_tipi,
                ek.yapildi,
                dk.diyet_tipi,
                dk.uygulandi,
                ek.kayit_tarihi
            FROM egzersiz_kayitlari ek
            JOIN kullanicilar k ON ek.hasta_id = k.kullanici_id
            LEFT JOIN diyet_kayitlari dk ON ek.hasta_id = dk.hasta_id 
                AND ek.kayit_tarihi = dk.kayit_tarihi
        """)
        print(tabulate(cur.fetchall(), 
                      headers=['Hasta Ad', 'Hasta Soyad', 'Egzersiz Tipi', 
                              'Yapıldı', 'Diyet Tipi', 'Uygulandı', 'Tarih'],
                      tablefmt='grid'))

        print("\n5. Belirtiler ve Uyarılar:")
        cur.execute("""
            SELECT 
                k.ad as hasta_ad,
                k.soyad as hasta_soyad,
                b.belirti_adi,
                u.uyari_tipi,
                u.uyari_mesaji,
                u.uyari_tarihi
            FROM hasta_belirtileri hb
            JOIN kullanicilar k ON hb.hasta_id = k.kullanici_id
            JOIN belirtiler b ON hb.belirti_id = b.belirti_id
            JOIN uyarilar u ON hb.hasta_id = u.hasta_id
        """)
        print(tabulate(cur.fetchall(), 
                      headers=['Hasta Ad', 'Hasta Soyad', 'Belirti', 
                              'Uyarı Tipi', 'Uyarı Mesajı', 'Uyarı Tarihi'],
                      tablefmt='grid'))

    except Exception as e:
        print("Hata oluştu:", e)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    test_queries() 