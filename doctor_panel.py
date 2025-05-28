import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QTableWidget, 
                            QTableWidgetItem, QTabWidget, QComboBox, QMessageBox, QLineEdit, QDialog, QFormLayout, QDateEdit, QRadioButton, QButtonGroup, QProgressBar, QDateTimeEdit)
from PyQt6.QtCore import Qt, QDate, QDateTime
from PyQt6.QtGui import QFont
import psycopg2
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

class DoctorPanel(QMainWindow):
    def __init__(self, user_id, user_name):
        super().__init__()
        self.user_id = user_id
        self.user_name = user_name
        self.setWindowTitle(f"Doktor Paneli - {user_name}")
        self.setMinimumSize(800, 600)
        
        # Ana widget ve layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Üst bilgi
        info_layout = QHBoxLayout()
        welcome_label = QLabel(f"Hoş Geldiniz, Dr. {user_name}")
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
        
        # Hasta Listesi Tab'ı
        patient_tab = QWidget()
        patient_layout = QVBoxLayout(patient_tab)
        
        # Hasta listesi tablosu
        self.patient_table = QTableWidget()
        self.patient_table.setColumnCount(5)
        self.patient_table.setHorizontalHeaderLabels(["TC", "Ad", "Soyad", "Email", "Son Ölçüm"])
        self.patient_table.horizontalHeader().setStretchLastSection(True)
        patient_layout.addWidget(self.patient_table)
        
        # Hasta detayları için buton
        view_button = QPushButton("Hasta Detaylarını Görüntüle")
        view_button.setStyleSheet("""
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
        view_button.clicked.connect(self.view_patient_details)
        patient_layout.addWidget(view_button)
        
        # Hasta ekle/sil alanı
        add_remove_layout = QHBoxLayout()
        self.add_patient_tc_input = QLineEdit()
        self.add_patient_tc_input.setPlaceholderText("Hasta TC Kimlik No")
        add_patient_button = QPushButton("Hasta Ekle")
        add_patient_button.setStyleSheet("background-color: #2196F3; color: white; padding: 6px; border-radius: 4px;")
        add_patient_button.clicked.connect(self.add_patient)
        remove_patient_button = QPushButton("Seçili Hastayı Sil")
        remove_patient_button.setStyleSheet("background-color: #f44336; color: white; padding: 6px; border-radius: 4px;")
        remove_patient_button.clicked.connect(self.remove_patient)
        add_remove_layout.addWidget(self.add_patient_tc_input)
        add_remove_layout.addWidget(add_patient_button)
        add_remove_layout.addWidget(remove_patient_button)
        patient_layout.addLayout(add_remove_layout)
        
        # Filtreleme alanı
        filter_layout = QHBoxLayout()
        self.min_glucose_input = QLineEdit()
        self.min_glucose_input.setPlaceholderText("Min Kan Şekeri")
        self.min_glucose_input.setFixedWidth(100)
        self.max_glucose_input = QLineEdit()
        self.max_glucose_input.setPlaceholderText("Max Kan Şekeri")
        self.max_glucose_input.setFixedWidth(100)
        self.filter_symptom_combo = QComboBox()
        self.filter_symptom_combo.addItem("Belirti Seçin (Hepsi)", None)
        filter_button = QPushButton("Filtrele")
        filter_button.setStyleSheet("background-color: #555; color: white; padding: 6px; border-radius: 4px;")
        filter_button.clicked.connect(self.load_patients) # Filtreleyince hastaları yeniden yükle
        filter_layout.addWidget(QLabel("Kan Şekeri Aralığı:"))
        filter_layout.addWidget(self.min_glucose_input)
        filter_layout.addWidget(QLabel("-"))
        filter_layout.addWidget(self.max_glucose_input)
        filter_layout.addWidget(QLabel("Belirti:"))
        filter_layout.addWidget(self.filter_symptom_combo)
        filter_layout.addWidget(filter_button)
        filter_layout.addStretch(1) # Sağda boşluk bırak
        patient_layout.addLayout(filter_layout)
        
        tab_widget.addTab(patient_tab, "Hasta Listesi")
        
        # Kan Şekeri Takibi Tab'ı
        glucose_tab = QWidget()
        glucose_layout = QVBoxLayout(glucose_tab)
        
        # Hasta seçimi
        patient_select_layout = QHBoxLayout()
        patient_select_layout.addWidget(QLabel("Hasta Seçin:"))
        self.patient_combo = QComboBox()
        self.patient_combo.currentIndexChanged.connect(self.load_glucose_data)
        patient_select_layout.addWidget(self.patient_combo)
        glucose_layout.addLayout(patient_select_layout)
        
        # Kan şekeri tablosu
        self.glucose_table = QTableWidget()
        self.glucose_table.setColumnCount(4)
        self.glucose_table.setHorizontalHeaderLabels(["Tarih", "Saat", "Ölçüm Tipi", "Değer"])
        self.glucose_table.horizontalHeader().setStretchLastSection(True)
        glucose_layout.addWidget(self.glucose_table)
        
        # Öneri Alanı
        recommendation_layout = QVBoxLayout()
        recommendation_layout.addWidget(QLabel("<b>Otomatik Öneriler:</b>")) # Başlık
        self.diet_recommendation_label = QLabel("Diyet Önerisi: Belirlenmedi")
        self.exercise_recommendation_label = QLabel("Egzersiz Önerisi: Belirlenmedi")
        self.insulin_recommendation_label = QLabel("İnsülin Önerisi: Belirlenmedi")

        recommendation_layout.addWidget(self.diet_recommendation_label)
        recommendation_layout.addWidget(self.exercise_recommendation_label)
        recommendation_layout.addWidget(self.insulin_recommendation_label)

        glucose_layout.addLayout(recommendation_layout) # Yeni alanı layout'a ekle
        
        # Kan şekeri ekleme alanı
        add_glucose_layout = QHBoxLayout()
        self.glucose_type_combo = QComboBox()
        self.glucose_type_combo.addItems(["SABAH", "OGLEN", "IKINDI", "AKSAM", "GECE"])
        self.glucose_value_input = QLineEdit()
        self.glucose_value_input.setPlaceholderText("Değer (mg/dL)")
        self.glucose_time_input = QDateTimeEdit()
        self.glucose_time_input.setCalendarPopup(True)
        self.glucose_time_input.setDateTime(QDateTime.currentDateTime())
        add_glucose_button = QPushButton("Kan Şekeri Kaydı Ekle")
        add_glucose_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 6px; border-radius: 4px;")
        add_glucose_button.clicked.connect(self.add_glucose_record)
        add_glucose_layout.addWidget(QLabel("Ölçüm Tipi:"))
        add_glucose_layout.addWidget(self.glucose_type_combo)
        add_glucose_layout.addWidget(QLabel("Değer:"))
        add_glucose_layout.addWidget(self.glucose_value_input)
        add_glucose_layout.addWidget(QLabel("Tarih:"))
        add_glucose_layout.addWidget(self.glucose_time_input)
        add_glucose_layout.addWidget(add_glucose_button)
        glucose_layout.addLayout(add_glucose_layout)
        
        tab_widget.addTab(glucose_tab, "Kan Şekeri Takibi")
        
        # Belirti ekleme alanı (Kan Şekeri Takibi sekmesinin altına ekleyeceğiz)
        # Bunun için yeni bir sekme ekliyorum
        symptoms_tab = QWidget()
        symptoms_layout = QVBoxLayout(symptoms_tab)
        # Hasta seçimi (belirti sekmesi)
        patient_select_layout3 = QHBoxLayout()
        patient_select_layout3.addWidget(QLabel("Hasta Seçin:"))
        self.patient_combo3 = QComboBox()
        self.patient_combo3.currentIndexChanged.connect(self.load_symptom_data)
        patient_select_layout3.addWidget(self.patient_combo3)
        symptoms_layout.addLayout(patient_select_layout3)
        # Belirti ekleme alanı
        add_symptom_layout = QHBoxLayout()
        self.symptom_combo = QComboBox()
        add_symptom_button = QPushButton("Belirti Ekle")
        add_symptom_button.setStyleSheet("background-color: #9C27B0; color: white; padding: 6px; border-radius: 4px;")
        add_symptom_button.clicked.connect(self.add_symptom_record)
        add_symptom_layout.addWidget(QLabel("Belirti:"))
        add_symptom_layout.addWidget(self.symptom_combo)
        add_symptom_layout.addWidget(add_symptom_button)
        symptoms_layout.addLayout(add_symptom_layout)
        # Belirti tablosu
        self.symptom_table = QTableWidget()
        self.symptom_table.setColumnCount(2)
        self.symptom_table.setHorizontalHeaderLabels(["Belirti", "Tarih"])
        self.symptom_table.horizontalHeader().setStretchLastSection(True)
        symptoms_layout.addWidget(self.symptom_table)
        tab_widget.addTab(symptoms_tab, "Belirti Kaydı")
        
        # Kan Şekeri Analizi Tab'ı
        analysis_tab = QWidget()
        analysis_layout = QVBoxLayout(analysis_tab)
        
        # Hasta seçimi
        patient_select_layout4 = QHBoxLayout()
        patient_select_layout4.addWidget(QLabel("Hasta Seçin:"))
        self.patient_combo4 = QComboBox()
        self.patient_combo4.currentIndexChanged.connect(self.load_analysis_data)
        patient_select_layout4.addWidget(self.patient_combo4)
        analysis_layout.addLayout(patient_select_layout4)
        
        # Grafik alanı
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        analysis_layout.addWidget(self.canvas)
        
        # Tarih aralığı seçimi
        date_range_layout = QHBoxLayout()
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        
        date_range_layout.addWidget(QLabel("Başlangıç:"))
        date_range_layout.addWidget(self.start_date)
        date_range_layout.addWidget(QLabel("Bitiş:"))
        date_range_layout.addWidget(self.end_date)
        
        update_button = QPushButton("Grafiği Güncelle")
        update_button.clicked.connect(self.update_analysis_graph)
        date_range_layout.addWidget(update_button)
        
        analysis_layout.addLayout(date_range_layout)
        
        tab_widget.addTab(analysis_tab, "Kan Şekeri Analizi")
        
        # Egzersiz ve Diyet Takibi Tab'ı
        exercise_diet_tab = QWidget()
        exercise_diet_layout = QVBoxLayout(exercise_diet_tab)
        
        # Hasta seçimi
        patient_select_layout2 = QHBoxLayout()
        patient_select_layout2.addWidget(QLabel("Hasta Seçin:"))
        self.patient_combo2 = QComboBox()
        self.patient_combo2.currentIndexChanged.connect(self.load_exercise_diet_data)
        patient_select_layout2.addWidget(self.patient_combo2)
        exercise_diet_layout.addLayout(patient_select_layout2)

        # Yüzdesel gösterim alanı
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
        self.exercise_diet_table.setColumnCount(4)
        self.exercise_diet_table.setHorizontalHeaderLabels(["Tarih", "Egzersiz", "Diyet", "Uygulama Durumu"])
        self.exercise_diet_table.horizontalHeader().setStretchLastSection(True)
        exercise_diet_layout.addWidget(self.exercise_diet_table)
        
        # Egzersiz ve diyet ekleme alanı
        add_exercise_diet_layout = QHBoxLayout()
        self.exercise_type_combo = QComboBox()
        self.exercise_type_combo.addItems(["YURUYUS", "BISIKLET", "KLINIK"])
        self.diet_type_combo = QComboBox()
        self.diet_type_combo.addItems(["AZ_SEKERLI", "SEKERSIZ", "DENGELI"])
        self.exercise_date_input = QDateEdit()
        self.exercise_date_input.setCalendarPopup(True)
        self.exercise_date_input.setDate(QDate.currentDate())
        add_exercise_button = QPushButton("Egzersiz Ekle")
        add_exercise_button.setStyleSheet("background-color: #2196F3; color: white; padding: 6px; border-radius: 4px;")
        add_exercise_button.clicked.connect(self.add_exercise_record)
        add_diet_button = QPushButton("Diyet Ekle")
        add_diet_button.setStyleSheet("background-color: #FF9800; color: white; padding: 6px; border-radius: 4px;")
        add_diet_button.clicked.connect(self.add_diet_record)
        add_exercise_diet_layout.addWidget(QLabel("Egzersiz Tipi:"))
        add_exercise_diet_layout.addWidget(self.exercise_type_combo)
        add_exercise_diet_layout.addWidget(QLabel("Diyet Tipi:"))
        add_exercise_diet_layout.addWidget(self.diet_type_combo)
        add_exercise_diet_layout.addWidget(QLabel("Tarih:"))
        add_exercise_diet_layout.addWidget(self.exercise_date_input)
        add_exercise_diet_layout.addWidget(add_exercise_button)
        add_exercise_diet_layout.addWidget(add_diet_button)
        exercise_diet_layout.addLayout(add_exercise_diet_layout)
        
        tab_widget.addTab(exercise_diet_tab, "Egzersiz ve Diyet Takibi")
        
        # Uyarılar Tab'ı
        warnings_tab = QWidget()
        warnings_layout = QVBoxLayout(warnings_tab)
        
        # Hasta seçimi
        patient_select_layout5 = QHBoxLayout()
        patient_select_layout5.addWidget(QLabel("Hasta Seçin:"))
        self.patient_combo5 = QComboBox()
        self.patient_combo5.currentIndexChanged.connect(self.load_warnings)
        patient_select_layout5.addWidget(self.patient_combo5)
        warnings_layout.addLayout(patient_select_layout5)
        
        # Uyarı tablosu
        self.warnings_table = QTableWidget()
        self.warnings_table.setColumnCount(5)
        self.warnings_table.setHorizontalHeaderLabels(["Tarih", "Uyarı Tipi", "Mesaj", "Durum", "İşlem"])
        self.warnings_table.horizontalHeader().setStretchLastSection(True)
        warnings_layout.addWidget(self.warnings_table)
        
        # Uyarı gönderme alanı
        send_warning_layout = QHBoxLayout()
        self.warning_type_combo = QComboBox()
        self.warning_type_combo.addItems(["Hipoglisemi Riski", "Hiperglisemi Riski", "Ölçüm Eksik", "Ölçüm Yetersiz"])
        self.warning_message = QLineEdit()
        self.warning_message.setPlaceholderText("Uyarı mesajı")
        send_warning_button = QPushButton("Uyarı Gönder")
        send_warning_button.clicked.connect(self.send_warning)
        send_warning_layout.addWidget(QLabel("Uyarı Tipi:"))
        send_warning_layout.addWidget(self.warning_type_combo)
        send_warning_layout.addWidget(QLabel("Mesaj:"))
        send_warning_layout.addWidget(self.warning_message)
        send_warning_layout.addWidget(send_warning_button)
        warnings_layout.addLayout(send_warning_layout)
        
        tab_widget.addTab(warnings_tab, "Uyarılar")
        
        layout.addWidget(tab_widget)
        
        # Verileri yükle
        self.load_patients()
        # Belirti listesini yükle (ComboBoxlar oluşturulduktan sonra)
        self.load_symptom_list()
        # İlk hastanın verilerini yüklemek için ComboBox signalini tetikle (eğer hasta varsa)
        if self.patient_combo.count() > 0:
             self.patient_combo.currentIndexChanged.emit(self.patient_combo.currentIndex())
        if self.patient_combo2.count() > 0:
             self.patient_combo2.currentIndexChanged.emit(self.patient_combo2.currentIndex())
        if self.patient_combo3.count() > 0:
             self.patient_combo3.currentIndexChanged.emit(self.patient_combo3.currentIndex())
        if self.patient_combo5.count() > 0:
             self.patient_combo5.currentIndexChanged.emit(self.patient_combo5.currentIndex())
        if self.patient_combo4.count() > 0:
             self.patient_combo4.currentIndexChanged.emit(self.patient_combo4.currentIndex())

    def load_patients(self):
        try:
            conn = psycopg2.connect(
                dbname="diyabet_takip",
                user="postgres",
                password="1",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()
            
            # Filtreleme değerlerini al
            min_glucose = self.min_glucose_input.text().strip()
            max_glucose = self.max_glucose_input.text().strip()
            selected_symptom_id = self.filter_symptom_combo.currentData()

            sql_query = """
                SELECT DISTINCT h.tc_kimlik, h.ad, h.soyad, h.email,
                       (SELECT MAX(olcum_zamani) FROM kan_sekeri_olcumleri WHERE hasta_id = h.kullanici_id) as son_olcum,
                       h.kullanici_id
                FROM kullanicilar h
                JOIN doktor_hasta_iliskisi di ON h.kullanici_id = di.hasta_id
            """
            sql_params = [self.user_id]
            where_clauses = ["di.doktor_id = %s"]

            # Kan şekeri filtresi
            if min_glucose or max_glucose:
                try:
                    min_g = int(min_glucose) if min_glucose else 0
                    max_g = int(max_glucose) if max_glucose else 9999 # Yüksek bir varsayılan
                    where_clauses.append("h.kullanici_id IN (SELECT hasta_id FROM kan_sekeri_olcumleri WHERE olcum_degeri BETWEEN %s AND %s)")
                    sql_params.extend([min_g, max_g])
                except ValueError:
                    QMessageBox.warning(self, "Uyarı", "Kan şekeri değerleri için geçerli sayılar giriniz!")
                    return

            # Belirti filtresi
            if selected_symptom_id is not None:
                 sql_query += " JOIN hasta_belirtileri hb ON h.kullanici_id = hb.hasta_id"
                 where_clauses.append("hb.belirti_id = %s")
                 sql_params.append(selected_symptom_id)

            if where_clauses:
                sql_query += " WHERE " + " AND ".join(where_clauses)

            sql_query += " ORDER BY h.ad, h.soyad"
            
            # Hastaları getir
            cur.execute(sql_query, tuple(sql_params))
            
            patients = cur.fetchall()
            
            # Tabloyu doldur
            self.patient_table.setRowCount(len(patients))
            for i, patient in enumerate(patients):
                for j, value in enumerate(patient[:5]):
                    if j == 4 and value:  # Son ölçüm tarihi
                        value = value.strftime("%d.%m.%Y %H:%M")
                    item = QTableWidgetItem(str(value) if value else "")
                    self.patient_table.setItem(i, j, item)
                
            # ComboBox'ları doldururken hasta_id atanacak
            # Filtreleme olduğu için ComboBox'ları tekrar doldurmayalım ki seçili değerler kaybolmasın.
            # Bunun yerine, eğer ComboBox'lar boşsa dolduralım (ilk yüklemede)
            if self.patient_combo.count() == 0:
                for patient in patients:
                     self.patient_combo.addItem(f"{patient[1]} {patient[2]}", patient[5])
                     self.patient_combo2.addItem(f"{patient[1]} {patient[2]}", patient[5])
                     self.patient_combo3.addItem(f"{patient[1]} {patient[2]}", patient[5])
                     self.patient_combo5.addItem(f"{patient[1]} {patient[2]}", patient[5])
                     self.patient_combo4.addItem(f"{patient[1]} {patient[2]}", patient[5])

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veriler yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
                
    def load_glucose_data(self):
        hasta_id = self.patient_combo.currentData()
        if not hasta_id:
            self.glucose_table.setRowCount(0)
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
            
            # Kan şekeri verilerini getir
            cur.execute("""
                SELECT 
                    DATE(olcum_zamani) as tarih,
                    TO_CHAR(olcum_zamani, 'HH24:MI') as saat,
                    olcum_tipi,
                    olcum_degeri
                FROM kan_sekeri_olcumleri
                WHERE hasta_id = %s
                ORDER BY olcum_zamani DESC
            """, (hasta_id,))
            
            data = cur.fetchall()
            
            # Tabloyu doldur
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
        hasta_id = self.patient_combo2.currentData()
        if not hasta_id:
            self.exercise_diet_table.setRowCount(0)
            self.exercise_progress.setValue(0)
            self.diet_progress.setValue(0)
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
            
            # Egzersiz ve diyet verilerini çek (JOIN kullanarak belirti_adi alınacak)
            cur.execute("""
                SELECT 
                    ek.kayit_tarihi,
                    ek.egzersiz_tipi,
                    dk.diyet_tipi,
                    CASE 
                        WHEN ek.yapildi AND dk.uygulandi THEN 'Tam Uygulandı'
                        WHEN ek.yapildi OR dk.uygulandi THEN 'Kısmen Uygulandı'
                        ELSE 'Uygulanmadı'
                    END as durum
                FROM egzersiz_kayitlari ek
                LEFT JOIN diyet_kayitlari dk ON ek.hasta_id = dk.hasta_id 
                    AND ek.kayit_tarihi = dk.kayit_tarihi
                WHERE ek.hasta_id = %s
                ORDER BY ek.kayit_tarihi DESC
            """, (hasta_id,))
            
            data = cur.fetchall()
            
            self.exercise_diet_table.setRowCount(len(data))
            for i, row in enumerate(data):
                for j, value in enumerate(row):
                    if j == 0:  # Tarih
                        value = value.strftime("%d.%m.%Y")
                    item = QTableWidgetItem(str(value))
                    self.exercise_diet_table.setItem(i, j, item)
                    
            # Uygulama oranlarını hesapla
            cur.execute("SELECT COUNT(*) FROM egzersiz_kayitlari WHERE hasta_id = %s", (hasta_id,))
            total_exercises = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM egzersiz_kayitlari WHERE hasta_id = %s AND yapildi = true", (hasta_id,))
            done_exercises = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM diyet_kayitlari WHERE hasta_id = %s", (hasta_id,))
            total_diets = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM diyet_kayitlari WHERE hasta_id = %s AND uygulandi = true", (hasta_id,))
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
            
            # Her iki ComboBox'ı da temizle
            self.symptom_combo.clear()
            self.filter_symptom_combo.clear()
            
            # İlk öğe olarak "Belirti Seçin (Hepsi)" ekle
            self.filter_symptom_combo.addItem("Belirti Seçin (Hepsi)", None)
            
            # Belirtileri her iki ComboBox'a ekle
            for row in cur.fetchall():
                self.symptom_combo.addItem(row[1], row[0])
                self.filter_symptom_combo.addItem(row[1], row[0])
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Belirti listesi yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals(): cur.close()
            if 'conn' in locals(): conn.close()

    def add_symptom_record(self):
        hasta_id = self.patient_combo3.currentData()
        if not hasta_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir hasta seçin!")
            return
        belirti_id = self.symptom_combo.currentData()
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
            # Kayıt ekle
            cur.execute("INSERT INTO hasta_belirtileri (hasta_id, belirti_id, kayit_tarihi) VALUES (%s, %s, %s)", (hasta_id, belirti_id, datetime.now().date()))
            conn.commit()
            QMessageBox.information(self, "Başarılı", "Belirti kaydı eklendi!")
            self.load_symptom_data()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt eklenirken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals(): cur.close()
            if 'conn' in locals(): conn.close()

    def load_symptom_data(self):
        hasta_id = self.patient_combo3.currentData()
        if not hasta_id:
            self.symptom_table.setRowCount(0)
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
                SELECT b.belirti_adi, hb.kayit_tarihi
                FROM hasta_belirtileri hb
                JOIN belirtiler b ON hb.belirti_id = b.belirti_id
                WHERE hb.hasta_id = %s
                ORDER BY hb.kayit_tarihi DESC
            """, (hasta_id,))
            data = cur.fetchall()
            self.symptom_table.setRowCount(len(data))
            for i, row in enumerate(data):
                self.symptom_table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.symptom_table.setItem(i, 1, QTableWidgetItem(str(row[1])))
        except Exception as e:
            self.symptom_table.setRowCount(0)
        finally:
            if 'cur' in locals(): cur.close()
            if 'conn' in locals(): conn.close()

    def view_patient_details(self):
        selected_row = self.patient_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir hasta seçin!")
            return
            
        tc = self.patient_table.item(selected_row, 0).text()
        name = self.patient_table.item(selected_row, 1).text()
        surname = self.patient_table.item(selected_row, 2).text()
        
        QMessageBox.information(self, "Hasta Detayları", 
                              f"TC: {tc}\nAd: {name}\nSoyad: {surname}\n\n"
                              "Detaylı bilgiler için ilgili sekmeleri kullanabilirsiniz.")

    def add_patient(self):
        tc = self.add_patient_tc_input.text().strip()
        if not tc or len(tc) != 11 or not tc.isdigit():
            QMessageBox.warning(self, "Uyarı", "Geçerli bir TC Kimlik No giriniz!")
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
            # Hasta var mı ve tipi HASTA mı?
            cur.execute("SELECT kullanici_id FROM kullanicilar WHERE tc_kimlik = %s AND kullanici_tipi = 'HASTA'", (tc,))
            result = cur.fetchone()
            if not result:
                # Hasta yoksa yeni hasta ekle
                if self.new_patient_form(tc):
                    # Formdan sonra tekrar kontrol et
                    cur.execute("SELECT kullanici_id FROM kullanicilar WHERE tc_kimlik = %s AND kullanici_tipi = 'HASTA'", (tc,))
                    result = cur.fetchone()
                    if not result:
                        QMessageBox.warning(self, "Uyarı", "Hasta eklenemedi!")
                        return
                else:
                    return
            hasta_id = result[0]
            # Zaten ekli mi?
            cur.execute("SELECT 1 FROM doktor_hasta_iliskisi WHERE doktor_id = %s AND hasta_id = %s", (self.user_id, hasta_id))
            if cur.fetchone():
                QMessageBox.information(self, "Bilgi", "Bu hasta zaten listenizde!")
                return
            # Ekle
            cur.execute("INSERT INTO doktor_hasta_iliskisi (doktor_id, hasta_id) VALUES (%s, %s)", (self.user_id, hasta_id))
            conn.commit()
            QMessageBox.information(self, "Başarılı", "Hasta başarıyla eklendi!")
            self.load_patients()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hasta eklenirken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals(): cur.close()
            if 'conn' in locals(): conn.close()

    def new_patient_form(self, tc):
        dialog = QDialog(self)
        dialog.setWindowTitle("Yeni Hasta Kaydı")
        form = QFormLayout(dialog)
        ad_input = QLineEdit()
        soyad_input = QLineEdit()
        email_input = QLineEdit()
        sifre_input = QLineEdit()
        sifre_input.setEchoMode(QLineEdit.EchoMode.Password)
        dogum_input = QDateEdit()
        dogum_input.setCalendarPopup(True)
        dogum_input.setDate(QDate(1990, 1, 1))
        cinsiyet_group = QButtonGroup(dialog)
        erkek_radio = QRadioButton("Erkek")
        kadin_radio = QRadioButton("Kadın")
        cinsiyet_group.addButton(erkek_radio)
        cinsiyet_group.addButton(kadin_radio)
        cinsiyet_layout = QHBoxLayout()
        cinsiyet_layout.addWidget(erkek_radio)
        cinsiyet_layout.addWidget(kadin_radio)
        form.addRow("Ad:", ad_input)
        form.addRow("Soyad:", soyad_input)
        form.addRow("Email:", email_input)
        form.addRow("Şifre:", sifre_input)
        form.addRow("Doğum Tarihi:", dogum_input)
        form.addRow("Cinsiyet:", cinsiyet_layout)
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Kaydet")
        cancel_btn = QPushButton("İptal")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        form.addRow(btn_layout)
        result = {}
        def kaydet():
            if not ad_input.text() or not soyad_input.text() or not email_input.text() or not sifre_input.text() or (not erkek_radio.isChecked() and not kadin_radio.isChecked()):
                QMessageBox.warning(dialog, "Uyarı", "Tüm alanları doldurun!")
                return
            result['ad'] = ad_input.text()
            result['soyad'] = soyad_input.text()
            result['email'] = email_input.text()
            result['sifre'] = sifre_input.text()
            result['dogum'] = dogum_input.date().toPyDate()
            result['cinsiyet'] = 'E' if erkek_radio.isChecked() else 'K'
            dialog.accept()
        ok_btn.clicked.connect(kaydet)
        cancel_btn.clicked.connect(dialog.reject)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                import hashlib
                conn = psycopg2.connect(
                    dbname="diyabet_takip",
                    user="postgres",
                    password="1",
                    host="localhost",
                    port="5432"
                )
                cur = conn.cursor()
                sifre_hash = hashlib.sha256(result['sifre'].encode()).hexdigest()
                cur.execute("INSERT INTO kullanicilar (tc_kimlik, ad, soyad, email, sifre, dogum_tarihi, cinsiyet, kullanici_tipi) VALUES (%s, %s, %s, %s, %s, %s, %s, 'HASTA')", (tc, result['ad'], result['soyad'], result['email'], sifre_hash, result['dogum'], result['cinsiyet']))
                conn.commit()
                return True
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Hasta eklenirken hata oluştu: {str(e)}")
                return False
            finally:
                if 'cur' in locals(): cur.close()
                if 'conn' in locals(): conn.close()
        return False

    def remove_patient(self):
        selected_row = self.patient_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen silmek için bir hasta seçin!")
            return
        tc = self.patient_table.item(selected_row, 0).text()
        try:
            conn = psycopg2.connect(
                dbname="diyabet_takip",
                user="postgres",
                password="1",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()
            # Hasta id'yi bul
            cur.execute("SELECT kullanici_id FROM kullanicilar WHERE tc_kimlik = %s", (tc,))
            result = cur.fetchone()
            if not result:
                QMessageBox.warning(self, "Uyarı", "Hasta bulunamadı!")
                return
            hasta_id = result[0]
            # İlişkiyi sil
            cur.execute("DELETE FROM doktor_hasta_iliskisi WHERE doktor_id = %s AND hasta_id = %s", (self.user_id, hasta_id))
            # Başka doktora bağlı değilse hastayı tamamen sil
            cur.execute("DELETE FROM kullanicilar WHERE kullanici_id = %s", (hasta_id,))
            conn.commit()
            QMessageBox.information(self, "Başarılı", "Hasta listenizden silindi!")
            self.load_patients()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hasta silinirken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals(): cur.close()
            if 'conn' in locals(): conn.close()

    def get_glucose_level(self, value):
        """Kan şekeri değerine göre seviyeyi belirler ve öneri/uyarı için ilgili aralığı döndürür."""
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

    def add_glucose_record(self):
        hasta_id = self.patient_combo.currentData()
        if not hasta_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir hasta seçin!")
            return
        try:
            value = int(self.glucose_value_input.text())
        except ValueError:
            QMessageBox.warning(self, "Uyarı", "Geçerli bir değer giriniz!")
            return
        olcum_tipi = self.glucose_type_combo.currentText()
        olcum_zamani = self.glucose_time_input.dateTime().toPyDateTime()
        
        # process_glucose_data ve check_daily_measurement_count fonksiyonları tarih objesi bekliyor.
        # olcum_zamani datetime objesi olduğu için sadece tarih kısmını gönderelim.
        olcum_tarihi_date = olcum_zamani.date()
        
        glucose_level_name = self.get_glucose_level(value)
        glucose_level = self.get_recommendation_level(value)
        try:
            conn = psycopg2.connect(
                dbname="diyabet_takip",
                user="postgres",
                password="1",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()
            
            # Veritabanına kaydederken tam datetime objesini kullanıyoruz
            cur.execute("INSERT INTO kan_sekeri_olcumleri (hasta_id, olcum_degeri, olcum_zamani, olcum_tipi) VALUES (%s, %s, %s, %s)", (hasta_id, value, olcum_zamani, olcum_tipi))
            conn.commit()
            
            # İnsülin önerisi hesaplamasını ekle
            self.calculate_and_suggest_insulin(hasta_id, olcum_tarihi_date, olcum_tipi)
            
            QMessageBox.information(self, "Başarılı", "Kan şekeri kaydı eklendi!")
            self.load_glucose_data()

            # Otomatik öneri ve uyarıları tetikle
            # Fonksiyonlar tarih beklediği için sadece tarih kısmını gönderiyoruz
            self.process_glucose_data(hasta_id, value, olcum_tipi, olcum_tarihi_date, glucose_level_name)

            # Günlük ölçüm sayısını kontrol et ve uyarı oluştur
            # Fonksiyon tarih beklediği için sadece tarih kısmını gönderiyoruz
            self.check_daily_measurement_count(hasta_id, olcum_tarihi_date)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt eklenirken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals(): cur.close()
            if 'conn' in locals(): conn.close()

    def check_daily_measurement_count(self, hasta_id, current_date):
        """Belirtilen tarihte hastanın ölçüm sayısını kontrol eder ve uyarı oluşturur."""
        try:
            conn = psycopg2.connect(
                dbname="diyabet_takip",
                user="postgres",
                password="1",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()

            # Belirtilen tarihteki ölçüm sayısını al
            cur.execute("""
                SELECT COUNT(*)
                FROM kan_sekeri_olcumleri
                WHERE hasta_id = %s
                AND DATE(olcum_zamani) = %s
            """, (hasta_id, current_date))
            olcum_sayisi = cur.fetchone()[0]

            # Tüm gün ölçüm yapılmamış (bu kontrolün gün sonunda yapılması daha doğru olur ama şimdilik anlık ekliyorum)
            # Anlık eklemede bu uyarıyı tetiklemek zor, bu kısmı şimdilik atlıyorum. Gün sonunda kontrol mekanizması gerektiği notunu düşelim.

            # 3'ten az ölçüm girilmişse uyarı oluştur
            if olcum_sayisi > 0 and olcum_sayisi < 3:
                uyari_tipi = "Yetersiz Günlük Ölçüm Uyarısı"
                uyari_mesaji = f"Hastanın {current_date.strftime('%d.%m.%Y')} tarihli kan şekeri ölçüm sayısı yetersiz ({olcum_sayisi}). Günlük en az 3 ölçüm yapılmalıdır."
                self.create_warning(hasta_id, uyari_tipi, uyari_mesaji)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Günlük ölçüm sayısı kontrol edilirken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals(): cur.close()
            if 'conn' in locals(): conn.close()

    def process_glucose_data(self, hasta_id, value, olcum_tipi, olcum_tarihi, glucose_level_name):
        """Kan şekeri verilerine göre diyet, egzersiz önerileri ve uyarıları oluşturur."""
        try:
            conn = psycopg2.connect(
                dbname="diyabet_takip",
                user="postgres",
                password="1",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()

            # Hastanın belirtilerini çek
            cur.execute("""
                SELECT b.belirti_adi
                FROM hasta_belirtileri hb
                JOIN belirtiler b ON hb.belirti_id = b.belirti_id
                WHERE hb.hasta_id = %s
                AND DATE(hb.kayit_tarihi) = %s
            """, (hasta_id, olcum_tarihi))
            belirtiler = [row[0] for row in cur.fetchall()]

            # Kan şekeri seviyesini öneri/uyarı aralıklarına göre al
            glucose_rec_level = self.get_recommendation_level(value)

            # Diyet ve Egzersiz Önerileri (Dökümantasyondaki tabloya göre)
            diyet_onerisi = "Belirlenmedi"
            egzersiz_onerisi = "Belirlenmedi"

            if glucose_rec_level == "< 70":
                diyet_onerisi = "Dengeli Beslenme"
                egzersiz_onerisi = "Yok"
            elif glucose_rec_level == "70-110":
                if "Yorgunluk" in belirtiler or "Kilo Kaybı" in belirtiler:
                     diyet_onerisi = "Az Şekerli Diyet"
                     egzersiz_onerisi = "Yürüyüş"
                elif "Polifaji" in belirtiler or "Polidipsi" in belirtiler:
                     diyet_onerisi = "Dengeli Beslenme"
                     egzersiz_onerisi = "Yürüyüş"
                else: # Belirti yoksa
                     diyet_onerisi = "Dengeli Beslenme"
                     egzersiz_onerisi = "Yürüyüş"
            elif glucose_rec_level == "110-180":
                if "Bulanık Görme" in belirtiler or "Nöropati" in belirtiler:
                    diyet_onerisi = "Az Şekerli Diyet"
                    egzersiz_onerisi = "Klinik Egzersiz"
                elif "Poliüri" in belirtiler or "Polidipsi" in belirtiler:
                    diyet_onerisi = "Şekersiz Diyet"
                    egzersiz_onerisi = "Klinik Egzersiz"
                elif any(b in belirtiler for b in ["Yorgunluk", "Nöropati", "Bulanık Görme"]):
                     diyet_onerisi = "Az Şekerli Diyet"
                     egzersiz_onerisi = "Yürüyüş"
                else: # Belirti yoksa
                     diyet_onerisi = "Az Şekerli Diyet"
                     egzersiz_onerisi = "Yürüyüş"
            elif glucose_rec_level == ">= 180":
                 if any(b in belirtiler for b in ["Yaraların Yavaş İyileşmesi", "Polifaji", "Polidipsi"]):
                     diyet_onerisi = "Şekersiz Diyet"
                     egzersiz_onerisi = "Klinik Egzersiz"
                 elif any(b in belirtiler for b in ["Yaraların Yavaş İyileşmesi", "Kilo Kaybı"]):
                     diyet_onerisi = "Şekersiz Diyet"
                     egzersiz_onerisi = "Yürüyüş"
                 else: # Belirti yoksa
                     diyet_onerisi = "Şekersiz Diyet"
                     egzersiz_onerisi = "Klinik Egzersiz" # Yüksek seviyede belirti yoksa Klinik Egzersiz varsaydım.

            # Uyarı Oluşturma (Dökümantasyondaki tabloya göre)
            uyari_tipi = ""
            uyari_mesaji = ""

            if glucose_rec_level == "< 70":
                uyari_tipi = "Hipoglisemi Acil Uyarısı"
                uyari_mesaji = f"Hastanın kan şekeri seviyesi {value} mg/dL ile çok düşük. Hipoglisemi riski! Hızlı müdahale gerekebilir."
                self.create_warning(hasta_id, uyari_tipi, uyari_mesaji)
            elif glucose_rec_level == ">= 180":
                uyari_tipi = "Hiperglisemi Acil Müdahale Uyarısı"
                uyari_mesaji = f"Hastanın kan şekeri {value} mg/dL ile çok yüksek. Hiperglisemi durumu. Acil müdahale gerekebilir."
                self.create_warning(hasta_id, uyari_tipi, uyari_mesaji)
            elif glucose_rec_level == "110-180":
                uyari_tipi = "Yüksek Kan Şekeri İzleme Uyarısı"
                uyari_mesaji = f"Hastanın kan şekeri {value} mg/dL aralığında seyrediyor. Durum izlenmeli ve gerekli önlemler alınmalı."
                self.create_warning(hasta_id, uyari_tipi, uyari_mesaji)
            # Not: 70-110 aralığı için dökümantasyonda spesifik bir uyarı belirtilmemiş.

            # Günlük ölçüm sayısı yetersiz uyarısı kontrolü
            # Bu kontrolü her kan şekeri kaydı eklendiğinde yapmak yerine gün sonunda yapmak daha mantıklı.
            # Ancak anlık kontrol gerektiği için, güne ait ilk 3 ölçümden sonra yetersiz uyarısı verilebilir.
            # Daha doğru bir implementasyon için, gün sonunda tetiklenen bir mekanizma kurulmalıdır.
            # Geçici olarak, 3'ten az ölçüm girildiğinde (ama en az 1 ölçüm varsa) uyarı verelim.
            cur.execute("""
                SELECT COUNT(*)
                FROM kan_sekeri_olcumleri
                WHERE hasta_id = %s
                AND DATE(olcum_zamani) = %s
            """, (hasta_id, olcum_tarihi))
            olcum_sayisi = cur.fetchone()[0]

            if olcum_sayisi > 0 and olcum_sayisi < 3:
                uyari_tipi = "Yetersiz Günlük Ölçüm Uyarısı"
                uyari_mesaji = f"Hastanın {olcum_tarihi.strftime('%d.%m.%Y')} tarihli kan şekeri ölçüm sayısı yetersiz ({olcum_sayisi}). Günlük en az 3 ölçüm yapılmalıdır."
                self.create_warning(hasta_id, uyari_tipi, uyari_mesaji)

            # İnsülin önerisi (calculate_and_suggest_insulin içinde zaten yapılıyor)
            # self.calculate_and_suggest_insulin(hasta_id, olcum_tarihi, olcum_tipi)

            # Diyet ve egzersiz önerilerini UI'da göster
            self.diet_recommendation_label.setText(f"Diyet Önerisi: {diyet_onerisi}")
            self.exercise_recommendation_label.setText(f"Egzersiz Önerisi: {egzersiz_onerisi}")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri işlenirken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals(): cur.close()
            if 'conn' in locals(): conn.close()

    def calculate_and_suggest_insulin(self, hasta_id, current_date, current_olcum_tipi):
        """Günlük kan şekeri ortalamasına göre insülin önerisi hesaplar ve gösterir."""
        try:
            conn = psycopg2.connect(
                dbname="diyabet_takip",
                user="postgres",
                password="1",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()

            # Belirtilen tarihteki ve ilgili ölçüm tipine kadar olan ölçümleri al
            query = """
                SELECT olcum_degeri
                FROM kan_sekeri_olcumleri
                WHERE hasta_id = %s
                AND DATE(olcum_zamani) = %s
            """
            params = [hasta_id, current_date]

            # Ölçüm tipine göre filtreleme
            if current_olcum_tipi == "SABAH":
                query += " AND olcum_tipi = 'SABAH'"
            elif current_olcum_tipi == "OGLEN":
                query += " AND olcum_tipi IN ('SABAH', 'OGLEN')"
            elif current_olcum_tipi == "IKINDI":
                query += " AND olcum_tipi IN ('SABAH', 'OGLEN', 'IKINDI')"
            elif current_olcum_tipi == "AKSAM":
                query += " AND olcum_tipi IN ('SABAH', 'OGLEN', 'IKINDI', 'AKSAM')"
            elif current_olcum_tipi == "GECE":
                query += " AND olcum_tipi IN ('SABAH', 'OGLEN', 'IKINDI', 'AKSAM', 'GECE')"
            
            query += " ORDER BY olcum_zamani ASC"
            
            cur.execute(query, params)
            olcum_degerleri = [row[0] for row in cur.fetchall()]

            if not olcum_degerleri:
                self.insulin_recommendation_label.setText(f"İnsülin Önerisi ({current_olcum_tipi} Ort.): Ölçüm bulunamadı")
                return

            # Ortalama hesapla
            ortalama_kan_sekeri = sum(olcum_degerleri) / len(olcum_degerleri)

            # İnsülin önerisi belirle
            insulin_onerisi = "Yok"
            if 111 <= ortalama_kan_sekeri <= 150:
                insulin_onerisi = "1 ml"
            elif 151 <= ortalama_kan_sekeri <= 200:
                insulin_onerisi = "2 ml"
            elif ortalama_kan_sekeri > 200:
                insulin_onerisi = "3 ml"

            # İnsülin önerisini göster
            self.insulin_recommendation_label.setText(
                f"İnsülin Önerisi ({current_olcum_tipi} Ort.): {insulin_onerisi} "
                f"(Ortalama: {ortalama_kan_sekeri:.2f} mg/dL)"
            )

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"İnsülin önerisi hesaplanırken hata oluştu: {str(e)}")
            self.insulin_recommendation_label.setText(f"İnsülin Önerisi ({current_olcum_tipi} Ort.): Hesaplama Hatası")
        finally:
            if 'cur' in locals(): cur.close()
            if 'conn' in locals(): conn.close()

    def create_warning(self, hasta_id, uyari_tipi, uyari_mesaji):
        """Veritabanına yeni bir uyarı kaydı ekler."""
        try:
            conn = psycopg2.connect(
                dbname="diyabet_takip",
                user="postgres",
                password="1",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()
            from datetime import datetime
            cur.execute("INSERT INTO uyarilar (hasta_id, uyari_zamani, uyari_tipi, uyari_mesaji, okundu) VALUES (%s, %s, %s, %s, %s)",
                        (hasta_id, datetime.now(), uyari_tipi, uyari_mesaji, False))
            conn.commit()
            # QMessageBox.information(self, "Bilgi", f"Yeni uyarı oluşturuldu: {uyari_tipi}") # Test için eklenebilir
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Uyarı oluşturulurken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals(): cur.close()
            if 'conn' in locals(): conn.close()

    def load_analysis_data(self):
        hasta_id = self.patient_combo4.currentData()
        if not hasta_id:
            return
        self.update_analysis_graph()

    def update_analysis_graph(self):
        hasta_id = self.patient_combo4.currentData()
        if not hasta_id:
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

            # Kan şekeri verilerini al
            cur.execute("""
                SELECT olcum_zamani, olcum_degeri, olcum_tipi
                FROM kan_sekeri_olcumleri
                WHERE hasta_id = %s AND olcum_zamani BETWEEN %s AND %s
                ORDER BY olcum_zamani
            """, (hasta_id, self.start_date.date().toPyDate(), self.end_date.date().toPyDate()))
            glucose_data = cur.fetchall()

            # Egzersiz verilerini al
            cur.execute("""
                SELECT kayit_tarihi, egzersiz_tipi, yapildi
                FROM egzersiz_kayitlari
                WHERE hasta_id = %s AND kayit_tarihi BETWEEN %s AND %s
                ORDER BY kayit_tarihi
            """, (hasta_id, self.start_date.date().toPyDate(), self.end_date.date().toPyDate()))
            exercise_data = cur.fetchall()

            # Diyet verilerini al
            cur.execute("""
                SELECT kayit_tarihi, diyet_tipi, uygulandi
                FROM diyet_kayitlari
                WHERE hasta_id = %s AND kayit_tarihi BETWEEN %s AND %s
                ORDER BY kayit_tarihi
            """, (hasta_id, self.start_date.date().toPyDate(), self.end_date.date().toPyDate()))
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

    def add_exercise_record(self):
        """Egzersiz kaydını veritabanına ekler."""
        hasta_id = self.patient_combo2.currentData()
        if not hasta_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir hasta seçin!")
            return

        egzersiz_tipi = self.exercise_type_combo.currentText()
        tarih = self.exercise_date_input.date().toPyDate()

        try:
            conn = psycopg2.connect(
                dbname="diyabet_takip",
                user="postgres",
                password="1",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()

            # Egzersiz kaydını ekle (başlangıçta tamamlanmamış - False)
            cur.execute("INSERT INTO egzersiz_kayitlari (hasta_id, egzersiz_tipi, yapildi, kayit_tarihi) VALUES (%s, %s, %s, %s)",
                        (hasta_id, egzersiz_tipi, False, tarih)) # Burayı False yaptık
            conn.commit()

            QMessageBox.information(self, "Başarılı", "Egzersiz kaydı başarıyla eklendi!")
            self.load_exercise_diet_data() # Egzersiz/Diyet tablosunu yenile

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Egzersiz kaydı eklenirken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals(): cur.close()
            if 'conn' in locals(): conn.close()

    def add_diet_record(self):
        """Diyet kaydını veritabanına ekler."""
        hasta_id = self.patient_combo2.currentData()
        if not hasta_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir hasta seçin!")
            return

        diyet_tipi = self.diet_type_combo.currentText()
        tarih = self.exercise_date_input.date().toPyDate() # Aynı tarih inputunu kullanıyoruz

        try:
            conn = psycopg2.connect(
                dbname="diyabet_takip",
                user="postgres",
                password="1",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()

            # Diyet kaydını ekle (başlangıçta tamamlanmamış - False)
            cur.execute("INSERT INTO diyet_kayitlari (hasta_id, diyet_tipi, uygulandi, kayit_tarihi) VALUES (%s, %s, %s, %s)",
                        (hasta_id, diyet_tipi, False, tarih)) # Burayı False yaptık
            conn.commit()

            QMessageBox.information(self, "Başarılı", "Diyet kaydı başarıyla eklendi!")
            self.load_exercise_diet_data() # Egzersiz/Diyet tablosunu yenile

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Diyet kaydı eklenirken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals(): cur.close()
            if 'conn' in locals(): conn.close()

    def load_warnings(self):
        """Hastaya ait uyarıları veritabanından çeker ve tabloya yükler."""
        hasta_id = self.patient_combo5.currentData()
        if not hasta_id:
            self.warnings_table.setRowCount(0)
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
                SELECT uyari_id, uyari_zamani, uyari_tipi, uyari_mesaji, okundu
                FROM uyarilar
                WHERE hasta_id = %s
                ORDER BY uyari_zamani DESC
            """, (hasta_id,))

            warnings = cur.fetchall()
            self.warnings_table.setRowCount(len(warnings))

            for row, warning in enumerate(warnings):
                # Tarih
                self.warnings_table.setItem(row, 0, QTableWidgetItem(warning[1].strftime("%d.%m.%Y %H:%M")))
                # Uyarı tipi
                self.warnings_table.setItem(row, 1, QTableWidgetItem(warning[2]))
                # Mesaj
                self.warnings_table.setItem(row, 2, QTableWidgetItem(warning[3]))
                # Durum
                status = "Okundu" if warning[4] else "Okunmadı"
                self.warnings_table.setItem(row, 3, QTableWidgetItem(status))

                # İşlem butonu
                action_button = QPushButton("Okundu İşaretle")
                action_button.setEnabled(not warning[4])
                action_button.clicked.connect(lambda checked, id=warning[0]: self.mark_warning_as_read(id))
                self.warnings_table.setCellWidget(row, 4, action_button)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Uyarılar yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()

    def mark_warning_as_read(self, warning_id):
        """Belirtilen uyarıyı 'okundu' olarak işaretler."""
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
            self.load_warnings() # Uyarılar tablosunu yenile

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Uyarı 'okundu' olarak işaretlenirken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals(): cur.close()
            if 'conn' in locals(): conn.close()

    def send_warning(self):
        """Seçilen hastaya uyarı gönderir (veritabanına kaydeder)."""
        hasta_id = self.patient_combo5.currentData()
        if not hasta_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir hasta seçin!")
            return

        uyari_tipi = self.warning_type_combo.currentText()
        uyari_mesaji = self.warning_message.text().strip()

        if not uyari_mesaji:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir uyarı mesajı girin!")
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
            from datetime import datetime
            cur.execute("INSERT INTO uyarilar (hasta_id, uyari_zamani, uyari_tipi, uyari_mesaji, okundu) VALUES (%s, %s, %s, %s, %s)",
                        (hasta_id, datetime.now(), uyari_tipi, uyari_mesaji, False))
            conn.commit()
            QMessageBox.information(self, "Başarılı", "Uyarı başarıyla gönderildi!")
            self.warning_message.clear() # Mesaj kutusunu temizle
            self.load_warnings() # Uyarılar tablosunu yenile

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Uyarı gönderilirken hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()

def main():
    app = QApplication(sys.argv)
    window = DoctorPanel(1, "Ahmet Yılmaz")  # Test için
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 