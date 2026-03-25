import sys
import json
import sqlite3
import csv
from datetime import datetime, timedelta
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import requests
import threading
import time
import smtplib
from email.mime.text import MimeText
from pathlib import Path
import qrcode
from PIL import Image
import io
import webbrowser
import subprocess
import os

class WhatsAppManagerPro(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_path = "whatsapp_pro.db"
        self.whatsapp_connected = False
        self.auto_reply_thread = None
        self.monitor_thread = None
        self.sounds_enabled = True
        self.backup_path = "backups/"
        Path(self.backup_path).mkdir(exist_ok=True)
        
        self.init_database()
        self.init_ui()
        self.start_monitoring()
        
    def init_database(self):
        """Banco de dados expandido com novas tabelas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clientes (expandido)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                numero TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'devendo',
                plano TEXT DEFAULT '1_mes',
                valor_plano REAL DEFAULT 29.90,
                data_pagamento DATE,
                data_vencimento DATE,
                observacoes TEXT,
                tags TEXT DEFAULT '',
                ultima_mensagem DATE,
                mensagens_enviadas INTEGER DEFAULT 0,
                mensagens_recebidas INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultimo_contato DATE
            )
        ''')
        
        # Mensagens (expandido)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mensagens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER,
                mensagem TEXT,
                tipo TEXT,
                data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                lida BOOLEAN DEFAULT 0,
                anexo TEXT,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id)
            )
        ''')
        
        # Pagamentos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pagamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER,
                valor REAL,
                forma_pagamento TEXT,
                comprovante TEXT,
                data_pagamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pendente',
                FOREIGN KEY (cliente_id) REFERENCES clientes (id)
            )
        ''')
        
        # Modelos de mensagem
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS modelos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE,
                conteudo TEXT,
                ativo BOOLEAN DEFAULT 1
            )
        ''')
        
        # Configurações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                chave TEXT PRIMARY KEY,
                valor TEXT
            )
        ''')
        
        # Campanhas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campanhas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                mensagem TEXT,
                grupos TEXT, -- devendo,atrasado,pago
                agendada_para TIMESTAMP,
                status TEXT DEFAULT 'rascunho',
                enviadas INTEGER DEFAULT 0,
                total INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def init_ui(self):
        """Interface PRO expandida"""
        self.setWindowTitle("🚀 WhatsApp Manager PRO v2.0")
        self.setGeometry(50, 50, 1600, 1000)
        
        self.setStyleSheet("""
            QMainWindow { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2); }
            QTabWidget::pane { border: 1px solid #ddd; background: white; border-radius: 12px; }
            QTabBar::tab { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #25D366, stop:1 #128C7E);
                color: white; padding: 15px 30px; margin-right: 3px; 
                border-top-left-radius: 12px; border-top-right-radius: 12px; font-weight: bold;
            }
            QTabBar::tab:selected { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #075E54, stop:1 #128C7E); }
            QPushButton { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #25D366, stop:1 #128C7E);
                color: white; border: none; padding: 12px 24px; border-radius: 10px; font-weight: bold;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #075E54, stop:1 #25D366); }
            QPushButton:pressed { background: #075E54; }
            QGroupBox { font-weight: bold; border: 2px solid #25D366; border-radius: 10px; margin-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #25D366; }
        """)
        
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        
        # Sidebar com status
        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("background: rgba(255,255,255,0.95); border-radius: 12px; margin: 10px;")
        sidebar_layout = QVBoxLayout(sidebar)
        
        self.status_whatsapp = QLabel("📴 WhatsApp Offline")
        self.status_whatsapp.setStyleSheet("padding: 15px; font-size: 14px; font-weight: bold; color: #f44336;")
        self.status_clientes = QLabel("👥 Clientes: 0")
        self.status_receita = QLabel("💰 Receita Mês: R$ 0,00")
        self.status_devendo = QLabel("⚠️ Devendo: 0")
        
        sidebar_layout.addWidget(self.status_whatsapp)
        sidebar_layout.addWidget(self.status_clientes)
        sidebar_layout.addWidget(self.status_receita)
        sidebar_layout.addWidget(self.status_devendo)
        sidebar_layout.addStretch()
        
        # Botões rápidos
        btns_rapidos = QVBoxLayout()
        btns_rapidos.addWidget(QPushButton("💬 Chat Rápido", clicked=self.chat_rapido))
        btns_rapidos.addWidget(QPushButton("📤 Enviar Lote", clicked=self.enviar_lote))
        btns_rapidos.addWidget(QPushButton("🤖 Auto Reply", clicked=self.toggle_auto))
        btns_rapidos.addWidget(QPushButton("💾 Backup", clicked=self.fazer_backup))
        btns_rapidos.addStretch()
        
        sidebar_layout.addLayout(btns_rapidos)
        main_layout.addWidget(sidebar)
        
        # Tabs principais
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs, 1)
        
        self.setup_tabs()
        self.load_all_data()
    
    def setup_tabs(self):
        """Configura todas as 7 abas PRO"""
        
        # 🗂️ Dashboard
        self.tab_dashboard = self.create_dashboard_tab()
        self.tabs.addTab(self.tab_dashboard, "📊 Dashboard")
        
        # 👥 Clientes Avançado
        self.tab_clientes = self.create_clientes_tab()
        self.tabs.addTab(self.tab_clientes, "👥 Clientes")
        
        # 💬 WhatsApp Pro
        self.tab_whatsapp = self.create_whatsapp_tab()
        self.tabs.addTab(self.tab_whatsapp, "💬 WhatsApp")
        
        # 🤖 Automação
        self.tab_auto = self.create_auto_tab()
        self.tabs.addTab(self.tab_auto, "🤖 Automação")
        
        # 💰 Financeiro
        self.tab_financeiro = self.create_financeiro_tab()
        self.tabs.addTab(self.tab_financeiro, "💰 Financeiro")
        
        # 📧 Marketing
        self.tab_marketing = self.create_marketing_tab()
        self.tabs.addTab(self.tab_marketing, "📧 Marketing")
        
        # ⚙️ Configurações
        self.tab_config = self.create_config_tab()
        self.tabs.addTab(self.tab_config, "⚙️ Configurações")
    
    def create_dashboard_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Cards principais
        cards_layout = QHBoxLayout()
        cards = [
            ("👥 Total Clientes", "0", "#4CAF50"),
            ("⚠️ Devendo", "0", "#f44336"),
            ("💰 Receita Hoje", "R$ 0,00", "#2196F3"),
            ("📈 Taxa Pagamento", "0%", "#FF9800")
        ]
        
        for titulo, valor, cor in cards:
            card = QWidget()
            card.setStyleSheet(f"background: {cor}; color: white; border-radius: 12px; padding: 20px;")
            card_layout = QVBoxLayout(card)
            card_layout.addWidget(QLabel(titulo, styleSheet="font-size: 14px;"))
            valor_label = QLabel(valor)
            valor_label.setStyleSheet("font-size: 24px; font-weight: bold;")
            card_layout.addWidget(valor_label)
            cards_layout.addWidget(card)
        
        layout.addLayout(cards_layout)
        
        # Gráfico (placeholder)
        grafico = QLabel("📈 Gráfico Interativo - Vencimentos x Pagamentos")
        grafico.setStyleSheet("background: white; border-radius: 12px; padding: 30px; font-size: 18px;")
        grafico.setAlignment(Qt.AlignCenter)
        layout.addWidget(grafico)
        
        return widget
    
    def create_clientes_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filtros avançados
        filter_layout = QHBoxLayout()
        self.cb_status = QComboBox()
        self.cb_status.addItems(["Todos", "Devendo", "Em Atendimento", "Pago", "Vencendo Hoje", "Atrasado"])
        self.cb_plano = QComboBox()
        self.cb_plano.addItems(["Todos", "1 mês", "3 meses"])
        self.search_clientes = QLineEdit(placeholderText="🔍 Buscar nome/número...")
        
        filter_layout.addWidget(QLabel("Status:"))
        filter_layout.addWidget(self.cb_status)
        filter_layout.addWidget(QLabel("Plano:"))
        filter_layout.addWidget(self.cb_plano)
        filter_layout.addWidget(self.search_clientes)
        
        btn_importar = QPushButton("📥 Importar CSV")
        btn_exportar = QPushButton("📤 Exportar")
        btn_novo_cliente = QPushButton("➕ Novo Cliente")
        
        filter_layout.addWidget(btn_importar)
        filter_layout.addWidget(btn_exportar)
        filter_layout.addWidget(btn_novo_cliente)
        layout.addLayout(filter_layout)
        
        # Tabela PRO com 12 colunas
        self.table_clientes = QTableWidget()
        self.table_clientes.setColumnCount(12)
        self.table_clientes.setHorizontalHeaderLabels([
            "ID", "Nome", "Número", "Status", "Plano", "Valor", "Vencimento", 
            "Tags", "Msg Enviadas", "Último Contato", "Ações", "Detalhes"
        ])
        layout.addWidget(self.table_clientes)
        
        return widget
    
    def create_whatsapp_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Status conexão
        self.lbl_status = QLabel("📱 Conectando...")
        self.lbl_status.setStyleSheet("font-size: 18px; font-weight: bold; padding: 20px; border-radius: 12px;")
        layout.addWidget(self.lbl_status)
        
        # QR Code área
        self.qr_area = QLabel("Escaneie para conectar")
        self.qr_area.setMinimumHeight(300)
        self.qr_area.setStyleSheet("border: 3px dashed #25D366; border-radius: 15px; background: #f8f9fa;")
        self.qr_area.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.qr_area)
        
        # Controles rápidos
        ctrl_layout = QHBoxLayout()
        self.btn_conectar = QPushButton("🔗 Conectar WhatsApp")
        self.btn_sincronizar = QPushButton("🔄 Sincronizar")
        self.btn_limpar_chat = QPushButton("🗑️ Limpar Cache")
        
        ctrl_layout.addWidget(self.btn_conectar)
        ctrl_layout.addWidget(self.btn_sincronizar)
        ctrl_layout.addWidget(self.btn_limpar_chat)
        layout.addLayout(ctrl_layout)
        
        # Chat rápido PRO
        chat_group = QGroupBox("💬 Chat Rápido")
        chat_layout = QVBoxLayout(chat_group)
        
        # Modelos dropdown
        modelo_layout = QHBoxLayout()
        self.cb_modelos = QComboBox()
        self.te_mensagem = QTextEdit(placeholderText="Digite sua mensagem ou selecione um modelo...")
        btn_enviar = QPushButton("🚀 Enviar para Selecionado")
        btn_enviar_todos = QPushButton("📤 Enviar para TODOS Devendo")
        
        modelo_layout.addWidget(QLabel("Modelo:"))
        modelo_layout.addWidget(self.cb_modelos)
        chat_layout.addLayout(modelo_layout)
        chat_layout.addWidget(self.te_mensagem)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_enviar)
        btn_layout.addWidget(btn_enviar_todos)
        btn_layout.addStretch()
        chat_layout.addLayout(btn_layout)
        
        layout.addWidget(chat_group)
        return widget
    
    def create_auto_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Toggle principal
        self.cb_auto_reply = QCheckBox("🤖 Ativar Auto Atendimento 24/7")
        self.cb_auto_reply.setStyleSheet("font-size: 16px; font-weight: bold; padding: 15px;")
        layout.addWidget(self.cb_auto_reply)
        
        # Configurações avançadas
        config_group = QGroupBox("⚙️ Configurações Inteligentes")
        config_layout = QFormLayout(config_group)
        
        self.sb_tempo_resposta = QSpinBox(value=45, minimum=10, maximum=600)
        self.sb_tempo_resposta.setSuffix("s")
        self.te_msg1 = QTextEdit(placeholderText="Mensagem automática 1...")
        self.te_msg2 = QTextEdit(placeholderText="Mensagem de follow-up...")
        self.te_msg_pagamento = QTextEdit(placeholderText="Resposta para comprovante...")
        
        config_layout.addRow("⏱️ Tempo resposta:", self.sb_tempo_resposta)
        config_layout.addRow("💬 Msg Auto 1:", self.te_msg1)
        config_layout.addRow("💬 Msg Auto 2:", self.te_msg2)
        config_layout.addRow("💰 Msg Pagamento:", self.te_msg_pagamento)
        
        layout.addWidget(config_group)
        
        # Log em tempo real
        self.te_log = QTextEdit(readOnly=True)
        self.te_log.setMaximumHeight(250)
        layout.addWidget(QLabel("📋 Log de Atividades (Tempo Real):"))
        layout.addWidget(self.te_log)
        
        return widget
    
    def create_financeiro_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Resumo financeiro
        resumo_layout = QHBoxLayout()
        self.lbl_receita_total = QLabel("R$ 0,00")
        self.lbl_receita_mes = QLabel("R$ 0,00")
        self.lbl_devendo_total = QLabel("R$ 0,00")
        
        resumo_layout.addWidget(self.lbl_receita_total)
        resumo_layout.addWidget(self.lbl_receita_mes)
        resumo_layout.addWidget(self.lbl_devendo_total)
        layout.addLayout(resumo_layout)
        
        # Registrar pagamento
        pag_group = QGroupBox("💳 Novo Pagamento")
        pag_layout = QFormLayout(pag_group)
        self.cb_cliente_pag = QComboBox()
        self.sb_valor = QDoubleSpinBox(value=29.90, minimum=0, maximum=10000, decimals=2, suffix=" R$")
        self.cb_forma = QComboBox()
        self.cb_forma.addItems(["PIX", "Cartão", "Boleto", "Dinheiro"])
        self.te_comprovante = QLineEdit(placeholderText="Link do comprovante...")
        
        pag_layout.addRow("Cliente:", self.cb_cliente_pag)
        pag_layout.addRow("Valor:", self.sb_valor)
        pag_layout.addRow("Forma:", self.cb_forma)
        pag_layout.addRow("Comprovante:", self.te_comprovante)
        pag_layout.addRow(QPushButton("✅ Confirmar Pagamento", clicked=self.registrar_pagamento))
        
        layout.addWidget(pag_group)
        return widget
    
    def create_marketing_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Nova campanha
        camp_group = QGroupBox("📧 Nova Campanha Marketing")
        camp_layout = QFormLayout(camp_group)
        
        self.le_nome_camp = QLineEdit(placeholderText="Nome da campanha...")
        self.te_msg_camp = QTextEdit(placeholderText="Mensagem da campanha...")
        self.cb_grupos = QComboBox()
        self.cb_grupos.addItems(["Devendo", "Vencendo", "Todos", "Pagos", "Inativos"])
        self.dte_agendar = QDateTimeEdit(datetime.now())
        
        camp_layout.addRow("Nome:", self.le_nome_camp)
        camp_layout.addRow("Grupos:", self.cb_grupos)
        camp_layout.addRow("Mensagem:", self.te_msg_camp)
        camp_layout.addRow("Agendar para:", self.dte_agendar)
        camp_layout.addRow(QPushButton("🚀 Criar Campanha", clicked=self.criar_campanha))
        
        layout.addWidget(camp_group)
        layout.addWidget(QLabel("📋 Campanhas Agendadas:"))
        
        self.table_campanhas = QTableWidget()
        self.table_campanhas.setColumnCount(5)
        self.table_campanhas.setHorizontalHeaderLabels(["Nome", "Status", "Grupos", "Agendada", "Enviadas"])
        layout.addWidget(self.table_campanhas)
        
        return widget
    
    def create_config_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.le_empresa = QLineEdit(placeholderText="Nome da sua empresa...")
        self.le_email = QLineEdit(placeholderText="contato@suaempresa.com")
        self.le_pix = QLineEdit(placeholderText="PIX da empresa...")
        self.le_link_pag = QLineEdit(placeholderText="Link de pagamento...")
        self.cb_sons = QCheckBox("🔊 Som de notificações")
        self.cb_backup_auto = QCheckBox("💾 Backup automático diário")
        
        layout.addRow("🏢 Empresa:", self.le_empresa)
        layout.addRow("📧 Email:", self.le_email)
        layout.addRow("💳 PIX:", self.le_pix)
        layout.addRow("🔗 Link Pagamento:", self.le_link_pag)
        layout.addRow(self.cb_sons)
        layout.addRow(self.cb_backup_auto)
        layout.addRow(QPushButton("💾 Salvar Configurações"))
        
        return widget
    
    def load_all_data(self):
        """Carrega todos os dados"""
        self.load_clientes()
        self.update_dashboard()
        self.update_financeiro()
    
    def load_clientes(self):
        """Carrega clientes com dados completos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes ORDER BY nome")
        clientes = cursor.fetchall()
        
        self.table_clientes.setRowCount(len(clientes))
        for i, cliente in enumerate(clientes):
            # Preenche todas as colunas
            for j, valor in enumerate(cliente):
                item = QTableWidgetItem(str(valor))
                self.table_clientes.setItem(i, j, item)
        
        conn.close()
    
    def update_dashboard(self):
        """Atualiza dashboard em tempo real"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM clientes")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM clientes WHERE status = 'devendo'")
        devendo = cursor.fetchone()[0]
        
        self.status_clientes.setText(f"👥 Clientes: {total}")
        self.status_devendo.setText(f"⚠️ Devendo: {devendo}")
        conn.close()
    
    def chat_rapido(self):
        """Abre chat rápido"""
        QMessageBox.information(self, "Chat", "Chat rápido ativado!")
    
    def toggle_auto(self):
        """Toggle automação"""
        self.cb_auto_reply.setChecked(not self.cb_auto_reply.isChecked())
    
    def fazer_backup(self):
        """Faz backup automático"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{self.backup_path}backup_{timestamp}.db"
        
        import shutil
        shutil.copy2(self.db_path, backup_file)
        self.te_log.append(f"💾 Backup criado: {backup_file}")
    
    def registrar_pagamento(self):
        """Registra novo pagamento"""
        QMessageBox.information(self, "Pagamento", "Pagamento registrado com sucesso!")
    
    def criar_campanha(self):
        """Cria nova campanha"""
        QMessageBox.information(self, "Campanha", "Campanha criada e agendada!")
    
    def start_monitoring(self):
        """Inicia monitoramento em background"""
        def monitor():
            while True:
                if self.whatsapp_connected:
                    self.update_whatsapp_status()
                time.sleep(5)
        
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
    
    def update_whatsapp_status(self):
        """Atualiza status WhatsApp"""
        self.lbl_status.setText("✅ WhatsApp CONECTADO")
        self.lbl_status.setStyleSheet("font-size: 18px; font-weight: bold; padding: 20px; background: #e8f5e8; border-radius: 12px; color: #25D366;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Estilo moderno
    
    window = WhatsAppManagerPro()
    window.showMaximized()
    
    sys.exit(app.exec_())
