import sys
import hashlib
import psycopg2
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QMessageBox, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Diyabet Takip Sistemi - Giriş")
        self.setFixedSize(400, 300)
        
        # Ana widget ve layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Başlık
        title_label = QLabel("Diyabet Takip Sistemi")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Kullanıcı tipi seçimi
        self.user_type_combo = QComboBox()
        self.user_type_combo.addItems(["Doktor", "Hasta"])
        self.user_type_combo.setFont(QFont("Arial", 10))
        layout.addWidget(self.user_type_combo)

        # TC Kimlik No
        tc_layout = QHBoxLayout()
        tc_label = QLabel("TC Kimlik No:")
        tc_label.setFont(QFont("Arial", 10))
        self.tc_input = QLineEdit()
        self.tc_input.setMaxLength(11)
        self.tc_input.setPlaceholderText("11 haneli TC Kimlik No")
        tc_layout.addWidget(tc_label)
        tc_layout.addWidget(self.tc_input)
        layout.addLayout(tc_layout)

        # Şifre
        password_layout = QHBoxLayout()
        password_label = QLabel("Şifre:")
        password_label.setFont(QFont("Arial", 10))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Şifrenizi giriniz")
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)

        # Giriş butonu
        login_button = QPushButton("Giriş Yap")
        login_button.setFont(QFont("Arial", 10))
        login_button.setStyleSheet("""
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
        login_button.clicked.connect(self.login)
        layout.addWidget(login_button)

        # Hata mesajı etiketi
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.error_label)

    def hash_password(self, password):
        """Şifreyi hash'ler"""
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self):
        tc = self.tc_input.text()
        password = self.password_input.text()
        user_type = self.user_type_combo.currentText()

        if not tc or not password:
            self.error_label.setText("Lütfen tüm alanları doldurunuz!")
            return

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

            # Kullanıcı kontrolü
            cur.execute("""
                SELECT kullanici_id, ad, soyad, kullanici_tipi 
                FROM kullanicilar 
                WHERE tc_kimlik = %s AND sifre = %s AND kullanici_tipi = %s
            """, (tc, self.hash_password(password), user_type.upper()))

            user = cur.fetchone()

            if user:
                self.error_label.setText("")
                QMessageBox.information(self, "Başarılı", f"Hoş geldiniz, {user[1]} {user[2]}!")
                # Kullanıcı tipine göre ilgili pencereyi aç
                if user[3] == "DOKTOR":
                    from doctor_panel import DoctorPanel
                    self.doctor_panel = DoctorPanel(user[0], f"{user[1]} {user[2]}")
                    self.doctor_panel.show()
                    self.close()
                elif user[3] == "HASTA":
                    from patient_panel import PatientPanel
                    self.patient_panel = PatientPanel(user[0], f"{user[1]} {user[2]}")
                    self.patient_panel.show()
                    self.close()
            else:
                self.error_label.setText("TC Kimlik No veya şifre hatalı!")

        except Exception as e:
            self.error_label.setText(f"Bir hata oluştu: {str(e)}")
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()

def main():
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 