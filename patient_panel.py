import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QTableWidget, 
                            QTableWidgetItem, QTabWidget, QComboBox, QMessageBox,
                            QLineEdit, QSpinBox, QDateTimeEdit, QTextEdit, QDateEdit,
                            QProgressBar, QCheckBox)
from PyQt6.QtCore import Qt, QDateTime, QDate
from PyQt6.QtGui import QFont
import psycopg2
from datetime import datetime

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

class PatientPanel(QMainWindow):
    def __init__(self, user_id, user_name):
        super().__init__()
        self.user_id = user_id
        self.user_name = user_name
        self.setWindowTitle(f"Hasta Paneli - {user_name}")
        self.setMinimumSize(800, 600)
        
        # Ana widget ve layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Üst bilgi
        info_layout = QHBoxLayout()
        welcome_label = QLabel(f"Hoş Geldiniz, {user_name}")
        welcome_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        info_layout.addWidget(welcome_label)
        
        # Çıkış butonu
        logout_button = QPushButton("Çıkış Yap")
        logout_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        logout_button.clicked.connect(self.close)
        info_layout.addWidget(logout_button)
        layout.addLayout(info_layout)
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # Kan Şekeri Ölçümü Tab'ı
        glucose_tab = QWidget()
        glucose_layout = QVBoxLayout(glucose_tab)
        
        # Ölçüm girişi
        input_layout = QHBoxLayout()
        
        # Ölçüm tipi
        self.measurement_type = QComboBox()
        self.measurement_type.addItems(["SABAH", "OGLEN", "IKINDI", "AKSAM", "GECE"])
        input_layout.addWidget(QLabel("Ölçüm Tipi:"))
        input_layout.addWidget(self.measurement_type)
        
        # Ölçüm değeri
        self.measurement_value = QSpinBox()
        self.measurement_value.setRange(40, 600)
        self.measurement_value.setValue(100)
        input_layout.addWidget(QLabel("Değer (mg/dL):"))
        input_layout.addWidget(self.measurement_value)
        
        # Ölçüm zamanı
        self.measurement_time = QDateTimeEdit()
        self.measurement_time.setDateTime(QDateTime.currentDateTime())
        input_layout.addWidget(QLabel("Ölçüm Zamanı:"))
        input_layout.addWidget(self.measurement_time)
        
        # Kaydet butonu
        save_button = QPushButton("Kaydet")
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        save_button.clicked.connect(self.save_glucose_measurement)
        input_layout.addWidget(save_button)
        
        glucose_layout.addLayout(input_layout)
        
        # Öneri Alanı
        recommendation_layout = QVBoxLayout()
        recommendation_layout.addWidget(QLabel("<b>Otomatik Öneriler:</b>")) # Başlık
        self.diet_recommendation_label = QLabel("Diyet Önerisi: Yükleniyor...")
        self.exercise_recommendation_label = QLabel("Egzersiz Önerisi: Yükleniyor...")
        self.insulin_recommendation_label = QLabel("İnsülin Önerisi: Yükleniyor...")

        recommendation_layout.addWidget(self.diet_recommendation_label)
        recommendation_layout.addWidget(self.exercise_recommendation_label)
        recommendation_layout.addWidget(self.insulin_recommendation_label)

        glucose_layout.addLayout(recommendation_layout) # Yeni alanı layout'a ekle
        
        # Kan şekeri tablosu
        self.glucose_table = QTableWidget()
        self.glucose_table.setColumnCount(4)
        self.glucose_table.setHorizontalHeaderLabels(["Tarih", "Saat", "Ölçüm Tipi", "Değer"])
        self.glucose_table.horizontalHeader().setStretchLastSection(True)
        glucose_layout.addWidget(self.glucose_table)
        
        tab_widget.addTab(glucose_tab, "Kan Şekeri Ölçümü")
        
        # Egzersiz ve Diyet Tab'ı
        exercise_diet_tab = QWidget()
        exercise_diet_layout = QVBoxLayout(exercise_diet_tab)
        
        # Yüzdesel gösterim alanını buraya taşıyalım, tablonun üzerinde olsun
        progress_layout = QHBoxLayout()
        
        # Egzersiz yüzdesi
        exercise_progress_layout = QVBoxLayout()
        exercise_progress_layout.addWidget(QLabel("Egzersiz Uygulama Oranı"))
        self.exercise_progress = QProgressBar()
        self.exercise_progress.setRange(0, 100)
        exercise_progress_layout.addWidget(self.exercise_progress)
        progress_layout.addLayout(exercise_progress_layout)
        
        # Diyet yüzdesi
        diet_progress_layout = QVBoxLayout()
        diet_progress_layout.addWidget(QLabel("Diyet Uygulama Oranı"))
        self.diet_progress = QProgressBar()
        self.diet_progress.setRange(0, 100)
        diet_progress_layout.addWidget(self.diet_progress)
        progress_layout.addLayout(diet_progress_layout)
        
        exercise_diet_layout.addLayout(progress_layout)

        # Egzersiz ve diyet tablosu
        self.exercise_diet_table = QTableWidget()
        self.exercise_diet_table.setColumnCount(5) # Sütun sayısını 5 yapıyoruz
        self.exercise_diet_table.setHorizontalHeaderLabels(["Tarih", "Egzersiz", "Diyet", "Egzersiz Yapıldı", "Diyet Uygulandı"]) # Başlıkları güncelliyoruz
        self.exercise_diet_table.horizontalHeader().setStretchLastSection(True)
        # Tablo hücrelerine tıklanabilir hale getirelim
        self.exercise_diet_table.cellClicked.connect(self.handle_exercise_diet_click)

        exercise_diet_layout.addWidget(self.exercise_diet_table)
        
        tab_widget.addTab(exercise_diet_tab, "Egzersiz ve Diyet")
        
        # Belirti ve Uyarılar Tab'ı
        symptoms_tab = QWidget()
        symptoms_layout = QVBoxLayout(symptoms_tab)
        
        # Belirti girişi
        symptom_layout = QHBoxLayout()
        
        self.symptom_type = QComboBox()
        self.load_symptom_list()
        symptom_layout.addWidget(QLabel("Belirti:"))
        symptom_layout.addWidget(self.symptom_type)
        
        save_symptom_button = QPushButton("Belirti Bildir")
        save_symptom_button.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        save_symptom_button.clicked.connect(self.save_symptom)
        symptom_layout.addWidget(save_symptom_button)
        
        symptom_layout.addLayout(symptom_layout)
        
        # Belirti tablosu
        self.symptom_table = QTableWidget()
        self.symptom_table.setColumnCount(2)
        self.symptom_table.setHorizontalHeaderLabels(["Belirti", "Tarih"])
        self.symptom_table.horizontalHeader().setStretchLastSection(True)
        symptoms_layout.addWidget(self.symptom_table)
        
        # Uyarılar tablosu
        self.warnings_table = QTableWidget()
        self.warnings_table.setColumnCount(4)
        self.warnings_table.setHorizontalHeaderLabels(["Tarih", "Uyarı Tipi", "Mesaj", "İşlem"])
        self.warnings_table.horizontalHeader().setStretchLastSection(True)
        symptoms_layout.addWidget(self.warnings_table)
        
        tab_widget.addTab(symptoms_tab, "Belirti ve Uyarılar")
        
        # Kan Şekeri Analizi sekmesini kur
        self.setup_analysis_tab(tab_widget)
        
        layout.addWidget(tab_widget)
        
        # Verileri yükle
        self.load_glucose_data()
        self.load_exercise_diet_data()
        self.load_warnings()
        self.load_symptom_data()
        
        # Önerileri yükle
        self.load_recommendations()
        
    # Belirti listesini veritabanından yükle
    def load_symptom_list(self):
        try:
            conn = psycopg2.connect(
                dbname="diyabet_takip",
                user="postgres",
                password="1",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()
            cur.execute("SELECT belirti_id, belirti_adi FROM belirtiler ORDER BY belirti_adi")
            self.symptom_type.clear()
            for row in cur.fetchall():
                self.symptom_type.addItem(row[1], row[0])
        except Exception as e:
             QMessageBox.critical(self, "Hata", f"Belirti listesi yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
                
    def save_glucose_measurement(self):
        try:
            conn = psycopg2.connect(
                dbname="diyabet_takip",
                user="postgres",
                password="1",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()
            
            measurement_time = self.measurement_time.dateTime().toPyDateTime()
            
            cur.execute("""
                INSERT INTO kan_sekeri_olcumleri (hasta_id, olcum_zamani, olcum_tipi, olcum_degeri)
                VALUES (%s, %s, %s, %s)
            """, (self.user_id, measurement_time, self.measurement_type.currentText(), 
                  self.measurement_value.value()))
            
            conn.commit()
            QMessageBox.information(self, "Başarılı", "Kan şekeri ölçümü kaydedildi!")
            self.load_glucose_data()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ölçüm kaydedilirken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
                
    def save_exercise(self):
        try:
            conn = psycopg2.connect(
                dbname="diyabet_takip",
                user="postgres",
                password="1",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()
            yapildi = True if self.exercise_done_combo.currentText() == "Yapıldı" else False
            cur.execute("""
                INSERT INTO egzersiz_kayitlari (hasta_id, kayit_tarihi, egzersiz_tipi, yapildi)
                VALUES (%s, CURRENT_DATE, %s, %s)
            """, (self.user_id, self.exercise_type.currentText(), yapildi))
            
            conn.commit()
            QMessageBox.information(self, "Başarılı", "Egzersiz kaydı eklendi!")
            self.load_exercise_diet_data()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Egzersiz kaydedilirken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
                
    def save_diet(self):
        try:
            conn = psycopg2.connect(
                dbname="diyabet_takip",
                user="postgres",
                password="1",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()
            uygulandi = True if self.diet_done_combo.currentText() == "Uygulandı" else False
            cur.execute("""
                INSERT INTO diyet_kayitlari (hasta_id, kayit_tarihi, diyet_tipi, uygulandi)
                VALUES (%s, CURRENT_DATE, %s, %s)
            """, (self.user_id, self.diet_type.currentText(), uygulandi))
            
            conn.commit()
            QMessageBox.information(self, "Başarılı", "Diyet kaydı eklendi!")
            self.load_exercise_diet_data()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Diyet kaydedilirken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
                
    # Belirti kaydını hasta_belirtileri tablosuna ekle
    def save_symptom(self):
        belirti_id = self.symptom_type.currentData()
        if not belirti_id:
             QMessageBox.warning(self, "Uyarı", "Lütfen bir belirti seçin!")
             return
        try:
            conn = psycopg2.connect(
                dbname="diyabet_takip",
                user="postgres",
                password="1",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO hasta_belirtileri (hasta_id, belirti_id, kayit_tarihi)
                VALUES (%s, %s, CURRENT_DATE)
            """, (self.user_id, belirti_id))
            
            conn.commit()
            QMessageBox.information(self, "Başarılı", "Belirti bildirimi kaydedildi!")
            self.load_symptom_data() # Kaydı ekledikten sonra tabloyu güncelle
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Belirti kaydedilirken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
                
    def load_glucose_data(self):
        try:
            conn = psycopg2.connect(
                dbname="diyabet_takip",
                user="postgres",
                password="1",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    DATE(olcum_zamani) as tarih,
                    TO_CHAR(olcum_zamani, 'HH24:MI') as saat,
                    olcum_tipi,
                    olcum_degeri
                FROM kan_sekeri_olcumleri
                WHERE hasta_id = %s
                ORDER BY olcum_zamani DESC
            """, (self.user_id,))
            
            data = cur.fetchall()
            
            self.glucose_table.setRowCount(len(data))
            for i, row in enumerate(data):
                for j, value in enumerate(row):
                    if j == 0:  # Tarih
                        value = value.strftime("%d.%m.%Y")
                    item = QTableWidgetItem(str(value))
                    self.glucose_table.setItem(i, j, item)
                    
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kan şekeri verileri yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
                
    def load_exercise_diet_data(self):
        try:
            conn = psycopg2.connect(
                dbname="diyabet_takip",
                user="postgres",
                password="1",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()

            # Tablonun sinyallerini geçici olarak devre dışı bırak
            self.exercise_diet_table.blockSignals(True)

            # Hastaya ait egzersiz ve diyet kayıtlarını çek
            cur.execute("""
                SELECT
                    ek.kayit_tarihi,
                    ek.egzersiz_tipi,
                    dk.diyet_tipi,
                    ek.yapildi,
                    dk.uygulandi
                FROM egzersiz_kayitlari ek
                LEFT JOIN diyet_kayitlari dk ON ek.hasta_id = dk.hasta_id
                    AND ek.kayit_tarihi = dk.kayit_tarihi
                WHERE ek.hasta_id = %s
                ORDER BY ek.kayit_tarihi DESC
            """, (self.user_id,))

            data = cur.fetchall()

            self.exercise_diet_table.setRowCount(len(data))
            for i, row in enumerate(data):
                kayit_tarihi, egzersiz_tipi, diyet_tipi, egzersiz_yapildi, diyet_uygulandi = row

                # Tarih
                date_item = QTableWidgetItem(kayit_tarihi.strftime("%d.%m.%Y"))
                self.exercise_diet_table.setItem(i, 0, date_item)

                # Egzersiz Tipi
                exercise_item = QTableWidgetItem(str(egzersiz_tipi) if egzersiz_tipi else "")
                self.exercise_diet_table.setItem(i, 1, exercise_item)

                # Diyet Tipi
                diet_item = QTableWidgetItem(str(diyet_tipi) if diyet_tipi else "")
                self.exercise_diet_table.setItem(i, 2, diet_item)

                # Egzersiz Yapıldı Checkbox
                exercise_checkbox = QCheckBox()
                # Checkbox sinyallerini geçici olarak devre dışı bırak
                exercise_checkbox.blockSignals(True)
                exercise_checkbox.setChecked(egzersiz_yapildi if egzersiz_yapildi is not None else False)
                # Checkbox sinyallerini tekrar etkinleştir
                exercise_checkbox.blockSignals(False)
                # Checkbox durum değiştiğinde sinyali yakalayalım ve satır indeksini gönderelim
                exercise_checkbox.stateChanged.connect(lambda state, current_row=i: self.update_exercise_status_by_row(state, current_row))
                self.exercise_diet_table.setCellWidget(i, 3, exercise_checkbox)

                # Diyet Uygulandı Checkbox
                diet_checkbox = QCheckBox()
                # Checkbox sinyallerini geçici olarak devre dışı bırak
                diet_checkbox.blockSignals(True)
                diet_checkbox.setChecked(diyet_uygulandi if diyet_uygulandi is not None else False)
                # Checkbox sinyallerini tekrar etkinleştir
                diet_checkbox.blockSignals(False)
                # Checkbox durum değiştiğinde sinyali yakalayalım ve satır indeksini gönderelim
                diet_checkbox.stateChanged.connect(lambda state, current_row=i: self.update_diet_status_by_row(state, current_row))
                self.exercise_diet_table.setCellWidget(i, 4, diet_checkbox)

            # Uygulama oranlarını hesapla (doktor panelinden kopyalanabilir)
            cur.execute("SELECT COUNT(*) FROM egzersiz_kayitlari WHERE hasta_id = %s", (self.user_id,))
            total_exercises = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM egzersiz_kayitlari WHERE hasta_id = %s AND yapildi = true", (self.user_id,))
            done_exercises = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM diyet_kayitlari WHERE hasta_id = %s", (self.user_id,))
            total_diets = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM diyet_kayitlari WHERE hasta_id = %s AND uygulandi = true", (self.user_id,))
            applied_diets = cur.fetchone()[0]

            exercise_percentage = (done_exercises / total_exercises * 100) if total_exercises > 0 else 0
            diet_percentage = (applied_diets / total_diets * 100) if total_diets > 0 else 0

            self.exercise_progress.setValue(round(exercise_percentage))
            self.diet_progress.setValue(round(diet_percentage))

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Egzersiz ve diyet verileri yüklenirken hata oluştu: {str(e)}")
            self.exercise_progress.setValue(0)
            self.diet_progress.setValue(0)
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()

            # Tablonun sinyallerini tekrar etkinleştir
            self.exercise_diet_table.blockSignals(False)

    def load_warnings(self):
        try:
            conn = psycopg2.connect(
                dbname="diyabet_takip",
                user="postgres",
                password="1",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    uyari_id,
                    uyari_zamani,
                    uyari_tipi,
                    uyari_mesaji,
                    okundu
                FROM uyarilar
                WHERE hasta_id = %s
                ORDER BY uyari_zamani DESC
            """, (self.user_id,))
            
            data = cur.fetchall()
            
            self.warnings_table.setRowCount(len(data))
            for i, row in enumerate(data):
                uyari_id = row[0]
                okundu_status = row[4]
                
                self.warnings_table.setItem(i, 0, QTableWidgetItem(row[1].strftime("%d.%m.%Y %H:%M")))
                self.warnings_table.setItem(i, 1, QTableWidgetItem(str(row[2])))
                self.warnings_table.setItem(i, 2, QTableWidgetItem(str(row[3])))
                
                action_button = QPushButton("Okundu İşaretle")
                action_button.setEnabled(not okundu_status)
                action_button.clicked.connect(lambda checked, id=uyari_id: self.mark_warning_as_read(id))
                self.warnings_table.setCellWidget(i, 3, action_button)
                    
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Uyarılar yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()

    def mark_warning_as_read(self, warning_id):
        try:
            conn = psycopg2.connect(
                dbname="diyabet_takip",
                user="postgres",
                password="1",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()

            cur.execute("UPDATE uyarilar SET okundu = TRUE WHERE uyari_id = %s", (warning_id,))
            conn.commit()

            QMessageBox.information(self, "Başarılı", "Uyarı okundu olarak işaretlendi!")
            self.load_warnings()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Uyarı 'okundu' olarak işaretlenirken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals(): cur.close()
            if 'conn' in locals(): conn.close()

    # Hasta belirti verilerini yükle
    def load_symptom_data(self):
        try:
            conn = psycopg2.connect(
                dbname="diyabet_takip",
                user="postgres",
                password="1",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()
            
            cur.execute("""
                SELECT b.belirti_adi, hb.kayit_tarihi
                FROM hasta_belirtileri hb
                JOIN belirtiler b ON hb.belirti_id = b.belirti_id
                WHERE hb.hasta_id = %s
                ORDER BY hb.kayit_tarihi DESC
            """, (self.user_id,))
            
            data = cur.fetchall()
            
            self.symptom_table.setRowCount(len(data))
            for i, row in enumerate(data):
                self.symptom_table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.symptom_table.setItem(i, 1, QTableWidgetItem(str(row[1])))
                    
        except Exception as e:
             QMessageBox.critical(self, "Hata", f"Belirti verileri yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()

    # Yeni fonksiyonları buraya ekleyeceğiz
    def load_recommendations(self):
        try:
            conn = psycopg2.connect(
                dbname="diyabet_takip",
                user="postgres",
                password="1",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()

            # Hastaya ait en son ölçümü bul
            cur.execute("""
                SELECT olcum_zamani, olcum_degeri, olcum_tipi
                FROM kan_sekeri_olcumleri
                WHERE hasta_id = %s
                ORDER BY olcum_zamani DESC
                LIMIT 1
            """, (self.user_id,))
            last_measurement = cur.fetchone()

            if last_measurement:
                olcum_zamani, olcum_degeri, olcum_tipi = last_measurement

                # Doktor panelindeki process_glucose_data mantığını burada tekrar uygulayarak
                # son ölçüme göre önerileri belirleyebiliriz.
                # Alternatif olarak, eğer doktor panelinde öneriler veritabanına kaydediliyorsa,
                # buradan o kayıtları çekebiliriz. Ancak mevcut kodda öneriler veritabanına kaydedilmiyor.
                # Bu yüzden, basitçe kan şekeri seviyesine göre önerileri belirleyelim.

                glucose_level_name = self.get_glucose_level(olcum_degeri)
                glucose_rec_level = self.get_recommendation_level(olcum_degeri)

                diyet_onerisi = "Belirlenmedi"
                egzersiz_onerisi = "Belirlenmedi"
                insulin_onerisi = "Belirlenmedi" # Hasta panelinde insülin önerisi göstermeyelim

                if glucose_rec_level == "< 70":
                    diyet_onerisi = "Dengeli Beslenme"
                    egzersiz_onerisi = "Yok"
                elif glucose_rec_level == "70-110":
                     diyet_onerisi = "Dengeli Beslenme veya Az Şekerli Diyet"
                     egzersiz_onerisi = "Yürüyüş"
                elif glucose_rec_level == "110-180":
                     diyet_onerisi = "Az Şekerli Diyet veya Şekersiz Diyet"
                     egzersiz_onerisi = "Yürüyüş veya Klinik Egzersiz"
                elif glucose_rec_level == ">= 180":
                     diyet_onerisi = "Şekersiz Diyet"
                     egzersiz_onerisi = "Klinik Egzersiz veya Yürüyüş" # Yüksek seviyede Klinik Egzersiz varsaydım.

                self.diet_recommendation_label.setText(f"Diyet Önerisi: {diyet_onerisi}")
                self.exercise_recommendation_label.setText(f"Egzersiz Önerisi: {egzersiz_onerisi}")
                self.insulin_recommendation_label.setText(f"En Son Ölçüm ({olcum_zamani.strftime('%d.%m.%Y %H:%M')}, {olcum_tipi}): {olcum_degeri} mg/dL - Durum: {glucose_level_name}") # Hasta kendi seviyesini görsün

            else:
                self.diet_recommendation_label.setText("Diyet Önerisi: Ölçüm bulunamadı.")
                self.exercise_recommendation_label.setText("Egzersiz Önerisi: Ölçüm bulunamadı.")
                self.insulin_recommendation_label.setText("En Son Ölçüm: Bulunamadı")


        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Öneriler yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals(): cur.close()
            if 'conn' in locals(): conn.close()

    # Doktor panelindeki get_glucose_level ve get_recommendation_level fonksiyonlarını da buraya kopyalayalım
    def get_glucose_level(self, value):
        """Kan şekeri değerine göre seviyeyi belirler."""
        if value < 70:
            return "Hipoglisemi (< 70 mg/dL)"
        elif 70 <= value <= 99:
            return "Normal Seviye (70-99 mg/dL)"
        elif 100 <= value <= 125:
            return "Prediyabet (100-125 mg/dL)"
        else: # value >= 126
            return "Diyabet (≥ 126 mg/dL)"

    def get_recommendation_level(self, value):
        """Öneri ve uyarılar için kullanılan kan şekeri aralığını belirler."""
        if value < 70:
            return "< 70"
        elif 70 <= value <= 110:
            return "70-110"
        elif 111 <= value <= 180:
            return "110-180"
        else: # value > 180
            return ">= 180"

    # Kan Şekeri Analizi Tab'ı kurulumu
    def setup_analysis_tab(self, tab_widget):
        analysis_tab = QWidget()
        analysis_layout = QVBoxLayout(analysis_tab)

        # Tarih aralığı seçimi
        date_range_layout = QHBoxLayout()
        self.analysis_start_date = QDateEdit()
        self.analysis_start_date.setCalendarPopup(True)
        self.analysis_start_date.setDate(QDate.currentDate().addDays(-30))
        self.analysis_end_date = QDateEdit()
        self.analysis_end_date.setCalendarPopup(True)
        self.analysis_end_date.setDate(QDate.currentDate())

        date_range_layout.addWidget(QLabel("Başlangıç:"))
        date_range_layout.addWidget(self.analysis_start_date)
        date_range_layout.addWidget(QLabel("Bitiş:"))
        date_range_layout.addWidget(self.analysis_end_date)

        update_button = QPushButton("Grafiği Güncelle")
        update_button.clicked.connect(self.update_analysis_graph)
        date_range_layout.addWidget(update_button)

        analysis_layout.addLayout(date_range_layout)

        # Grafik alanı
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        analysis_layout.addWidget(self.canvas)

        tab_widget.addTab(analysis_tab, "Kan Şekeri Analizi")

    def update_analysis_graph(self):
        try:
            conn = psycopg2.connect(
                dbname="diyabet_takip",
                user="postgres",
                password="1",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()

            # Kan şekeri verilerini al
            cur.execute("""
                SELECT olcum_zamani, olcum_degeri, olcum_tipi
                FROM kan_sekeri_olcumleri
                WHERE hasta_id = %s AND olcum_zamani BETWEEN %s AND %s
                ORDER BY olcum_zamani
            """, (self.user_id, self.analysis_start_date.date().toPyDate(), self.analysis_end_date.date().toPyDate()))
            glucose_data = cur.fetchall()

            # Egzersiz verilerini al
            cur.execute("""
                SELECT kayit_tarihi, egzersiz_tipi, yapildi
                FROM egzersiz_kayitlari
                WHERE hasta_id = %s AND kayit_tarihi BETWEEN %s AND %s
                ORDER BY kayit_tarihi
            """, (self.user_id, self.analysis_start_date.date().toPyDate(), self.analysis_end_date.date().toPyDate()))
            exercise_data = cur.fetchall()

            # Diyet verilerini al
            cur.execute("""
                SELECT kayit_tarihi, diyet_tipi, uygulandi
                FROM diyet_kayitlari
                WHERE hasta_id = %s AND kayit_tarihi BETWEEN %s AND %s
                ORDER BY kayit_tarihi
            """, (self.user_id, self.analysis_start_date.date().toPyDate(), self.analysis_end_date.date().toPyDate()))
            diet_data = cur.fetchall()

            # Grafiği temizle
            self.figure.clear()

            # Alt grafikler oluştur
            gs = self.figure.add_gridspec(3, 1, height_ratios=[2, 1, 1])
            ax1 = self.figure.add_subplot(gs[0])
            ax2 = self.figure.add_subplot(gs[1])
            ax3 = self.figure.add_subplot(gs[2])

            # Kan şekeri grafiği
            dates = [row[0] for row in glucose_data]
            values = [row[1] for row in glucose_data]
            types = [row[2] for row in glucose_data]

            ax1.plot(dates, values, 'b-', label='Kan Şekeri')
            ax1.set_title('Kan Şekeri Değişimi')
            ax1.set_ylabel('mg/dL')
            ax1.grid(True)

            # Egzersiz grafiği
            exercise_dates = [row[0] for row in exercise_data]
            exercise_done = [1 if row[2] else 0 for row in exercise_data]
            ax2.bar(exercise_dates, exercise_done, color='g', label='Egzersiz')
            ax2.set_title('Egzersiz Takibi')
            ax2.set_ylabel('Yapıldı/Yapılmadı')
            ax2.set_ylim(0, 1)

            # Diyet grafiği
            diet_dates = [row[0] for row in diet_data]
            diet_done = [1 if row[2] else 0 for row in diet_data]
            ax3.bar(diet_dates, diet_done, color='r', label='Diyet')
            ax3.set_title('Diyet Takibi')
            ax3.set_ylabel('Uygulandı/Uygulanmadı')
            ax3.set_ylim(0, 1)

            # Grafik düzenleme
            self.figure.tight_layout()
            self.canvas.draw()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Grafik oluşturulurken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()

    def handle_exercise_diet_click(self, row, column):
        # Bu metodun içeriği, tabloya tıklanıldığında ne yapılacağını belirler
        # Örneğin, seçilen satırın bilgilerini kullanarak diğer işlemler yapılabilir
        # Burada, seçilen satırın bilgilerini konsola yazdırabiliriz
        selected_row = self.exercise_diet_table.item(row, column)
        if selected_row:
            print(f"Seçilen satır: {selected_row.text()}")

    # Egzersiz durumunu satır indeksine göre güncelleme fonksiyonu
    def update_exercise_status_by_row(self, state, row):
        yapildi = state == Qt.CheckState.Checked.value # Checkbox durumu
        # İlgili satırdaki tarihi alalım
        kayit_tarihi_str = self.exercise_diet_table.item(row, 0).text()
        kayit_tarihi = datetime.strptime(kayit_tarihi_str, "%d.%m.%Y").date()

        try:
            conn = psycopg2.connect(
                dbname="diyabet_takip",
                user="postgres",
                password="1",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()

            # Sadece ilgili egzersiz kaydının yapildi durumunu güncelle (hasta_id ve kayit_tarihi ile)
            cur.execute("UPDATE egzersiz_kayitlari SET yapildi = %s WHERE hasta_id = %s AND kayit_tarihi = %s", (yapildi, self.user_id, kayit_tarihi))
            conn.commit()

            # Durum değiştiğinde progress barları ve tabloyu güncelle
            self.load_exercise_diet_data()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Egzersiz durumu güncellenirken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals(): cur.close()
            if 'conn' in locals(): conn.close()

    # Diyet durumunu satır indeksine göre güncelleme fonksiyonu
    def update_diet_status_by_row(self, state, row):
        uygulandi = state == Qt.CheckState.Checked.value # Checkbox durumu
        # İlgili satırdaki tarihi alalım
        kayit_tarihi_str = self.exercise_diet_table.item(row, 0).text()
        kayit_tarihi = datetime.strptime(kayit_tarihi_str, "%d.%m.%Y").date()

        try:
            conn = psycopg2.connect(
                dbname="diyabet_takip",
                user="postgres",
                password="1",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()

            # Sadece ilgili diyet kaydının uygulandi durumunu güncelle (hasta_id ve kayit_tarihi ile)
            cur.execute("UPDATE diyet_kayitlari SET uygulandi = %s WHERE hasta_id = %s AND kayit_tarihi = %s", (uygulandi, self.user_id, kayit_tarihi))
            conn.commit()

            # Durum değiştiğinde progress barları ve tabloyu güncelle
            self.load_exercise_diet_data()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Diyet durumu güncellenirken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals(): cur.close()
            if 'conn' in locals(): conn.close()

def main():
    app = QApplication(sys.argv)
    window = PatientPanel(2, "Ayşe Demir")  # Test için
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 