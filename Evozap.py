import sys
import json
import sqlite3
from datetime import datetime, timedelta
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import requests
import threading
import time
from pathlib import Path
import qrcode
from PIL import Image
import io

class WhatsAppManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_path = "whatsapp_manager.db"
        self.init_database()
        self.clientes = []
        self.whatsapp_session = None
        self.auto_reply_active = False
        self.init_ui()
        self.load_clientes()
        
    def init_database(self):
        """Inicializa o banco de dados SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de clientes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                numero TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'devendo', -- devendo, em_atendimento, pago
                plano TEXT DEFAULT '1_mes', -- 1_mes, 3_meses
                data_pagamento DATE,
                data_vencimento DATE,
                observacoes TEXT,
                ultima_mensagem DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de mensagens
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mensagens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER,
                mensagem TEXT,
                tipo TEXT, -- enviado, recebido
                data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def init_ui(self):
        """Inicializa a interface principal"""
        self.setWindowTitle("WhatsApp Manager Pro")
        self.setGeometry(100, 100, 1400, 900)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f2f5;
            }
            QTabWidget::pane {
                border: 1px solid #ddd;
                background: white;
            }
            QTabBar::tab {
                background: #25D366;
                color: white;
                padding: 12px 24px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background: #128C7E;
            }
            QPushButton {
                background-color: #25D366;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #128C7E;
            }
            QTableWidget {
                gridline-color: #eee;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #25D366;
                color: white;
                padding: 8px;
                border: none;
            }
        """)
        
        # Central widget e tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        self.tabs = QTabWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.tabs)
        
        # Aba 1: Clientes
        self.tab_clientes = QWidget()
        self.tabs.addTab(self.tab_clientes, "👥 Clientes")
        self.setup_clientes_tab()
        
        # Aba 2: WhatsApp
        self.tab_whatsapp = QWidget()
        self.tabs.addTab(self.tab_whatsapp, "📱 WhatsApp")
        self.setup_whatsapp_tab()
        
        # Aba 3: Auto Atendimento
        self.tab_auto = QWidget()
        self.tabs.addTab(self.tab_auto, "🤖 Auto Atendimento")
        self.setup_auto_tab()
        
        # Aba 4: Relatórios
        self.tab_relatorios = QWidget()
        self.tabs.addTab(self.tab_relatorios, "📊 Relatórios")
        self.setup_relatorios_tab()
    
    def setup_clientes_tab(self):
        """Configura aba de clientes"""
        layout = QVBoxLayout(self.tab_clientes)
        
        # Filtros
        filter_layout = QHBoxLayout()
        self.filter_status = QComboBox()
        self.filter_status.addItems(["Todos", "Devendo", "Em Atendimento", "Pago"])
        self.filter_status.currentTextChanged.connect(self.filtrar_clientes)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Pesquisar cliente...")
        self.search_input.textChanged.connect(self.filtrar_clientes)
        
        filter_layout.addWidget(QLabel("Status:"))
        filter_layout.addWidget(self.filter_status)
        filter_layout.addWidget(self.search_input)
        filter_layout.addStretch()
        
        btn_novo = QPushButton("➕ Novo Cliente")
        btn_novo.clicked.connect(self.novo_cliente_dialog)
        filter_layout.addWidget(btn_novo)
        
        layout.addLayout(filter_layout)
        
        # Tabela de clientes
        self.tabela_clientes = QTableWidget()
        self.tabela_clientes.setColumnCount(7)
        self.tabela_clientes.setHorizontalHeaderLabels([
            "Nome", "Número", "Status", "Plano", "Vencimento", "Última Msg", "Ações"
        ])
        layout.addWidget(self.tabela_clientes)
        
        # Botões de ação
        action_layout = QHBoxLayout()
        btn_enviar_msg = QPushButton("📤 Enviar Mensagem")
        btn_alterar_status = QPushButton("🔄 Alterar Status")
        btn_pagar = QPushButton("💰 Marcar como Pago")
        
        btn_enviar_msg.clicked.connect(self.enviar_mensagem_selecionado)
        btn_alterar_status.clicked.connect(self.alterar_status_selecionado)
        btn_pagar.clicked.connect(self.marcar_pago)
        
        action_layout.addWidget(btn_enviar_msg)
        action_layout.addWidget(btn_alterar_status)
        action_layout.addWidget(btn_pagar)
        layout.addLayout(action_layout)
    
    def setup_whatsapp_tab(self):
        """Configura aba WhatsApp"""
        layout = QVBoxLayout(self.tab_whatsapp)
        
        # Status WhatsApp
        self.whatsapp_status = QLabel("❌ WhatsApp Desconectado")
        self.whatsapp_status.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; background: #ffebee; border-radius: 8px;")
        layout.addWidget(self.whatsapp_status)
        
        # QR Code
        self.qr_label = QLabel("Escaneie o QR Code para conectar")
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setMinimumHeight(300)
        self.qr_label.setStyleSheet("border: 2px dashed #ccc; border-radius: 12px; background: #f9f9f9;")
        layout.addWidget(self.qr_label)
        
        # Controles
        btn_conectar = QPushButton("🔗 Conectar WhatsApp")
        btn_conectar.clicked.connect(self.conectar_whatsapp)
        btn_sincronizar = QPushButton("🔄 Sincronizar Contatos")
        btn_sincronizar.clicked.connect(self.sincronizar_contatos)
        
        ctrl_layout = QHBoxLayout()
        ctrl_layout.addWidget(btn_conectar)
        ctrl_layout.addWidget(btn_sincronizar)
        ctrl_layout.addStretch()
        layout.addLayout(ctrl_layout)
        
        # Chat rápido
        layout.addWidget(QLabel("💬 Chat Rápido:"))
        self.chat_input = QTextEdit()
        self.chat_input.setMaximumHeight(100)
        self.chat_input.setPlaceholderText("Digite sua mensagem...")
        
        chat_btn_layout = QHBoxLayout()
        btn_enviar_chat = QPushButton("📤 Enviar")
        btn_enviar_todos_devendo = QPushButton("📤 Para Todos Devendo")
        
        btn_enviar_chat.clicked.connect(self.enviar_chat_rapido)
        btn_enviar_todos_devendo.clicked.connect(self.enviar_para_devendo)
        
        chat_btn_layout.addWidget(self.chat_input)
        chat_btn_layout.addWidget(btn_enviar_chat)
        chat_btn_layout.addWidget(btn_enviar_todos_devendo)
        layout.addLayout(chat_btn_layout)
    
    def setup_auto_tab(self):
        """Configura aba Auto Atendimento"""
        layout = QVBoxLayout(self.tab_auto)
        
        # Toggle Auto Reply
        self.auto_toggle = QCheckBox("🤖 Ativar Atendimento Automático")
        self.auto_toggle.stateChanged.connect(self.toggle_auto_reply)
        layout.addWidget(self.auto_toggle)
        
        # Configurações Auto Reply
        settings_group = QGroupBox("Configurações de Auto Reply")
        settings_layout = QFormLayout(settings_group)
        
        self.tempo_resposta = QSpinBox()
        self.tempo_resposta.setRange(30, 300)
        self.tempo_resposta.setValue(60)
        self.tempo_resposta.setSuffix(" segundos")
        
        self.msg_auto1 = QTextEdit()
        self.msg_auto1.setMaximumHeight(80)
        self.msg_auto1.setPlainText("Olá! Não consegui responder no momento. Você está com algum problema no plano ou quer renovar? Digite 1 para plano mensal, 2 para trimestral.")
        
        self.msg_auto2 = QTextEdit()
        self.msg_auto2.setMaximumHeight(80)
        self.msg_auto2.setPlainText("Perfeito! Para confirmar o pagamento, me envie o comprovante ou acesse nosso link de pagamento.")
        
        settings_layout.addRow("Tempo de resposta:", self.tempo_resposta)
        settings_layout.addRow("Resposta automática 1:", self.msg_auto1)
        settings_layout.addRow("Resposta automática 2:", self.msg_auto2)
        
        layout.addWidget(settings_group)
        
        # Log de auto replies
        layout.addWidget(QLabel("📋 Log de Auto Replies:"))
        self.log_auto = QTextEdit()
        self.log_auto.setMaximumHeight(200)
        layout.addWidget(self.log_auto)
    
    def setup_relatorios_tab(self):
        """Configura aba Relatórios"""
        layout = QVBoxLayout(self.tab_relatorios)
        
        # Estatísticas
        stats_layout = QHBoxLayout()
        self.lbl_total = QLabel("Total: 0")
        self.lbl_devendo = QLabel("Devendo: 0")
        self.lbl_ativo = QLabel("Ativo: 0")
        self.lbl_vencendo = QLabel("Vencendo: 0")
        
        stats_layout.addWidget(self.lbl_total)
        stats_layout.addWidget(self.lbl_devendo)
        stats_layout.addWidget(self.lbl_ativo)
        stats_layout.addWidget(self.lbl_vencendo)
        layout.addLayout(stats_layout)
        
        # Gráfico simples (placeholder)
        self.grafico = QLabel("📈 Gráfico de vencimentos (implementar com matplotlib)")
        layout.addWidget(self.grafico)
        
        # Exportar
        btn_exportar = QPushButton("💾 Exportar Relatório")
        btn_exportar.clicked.connect(self.exportar_relatorio)
        layout.addWidget(btn_exportar)
    
    def novo_cliente_dialog(self):
        """Dialog para novo cliente"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Novo Cliente")
        dialog.setFixedSize(400, 500)
        
        layout = QFormLayout(dialog)
        
        nome = QLineEdit()
        numero = QLineEdit()
        numero.setPlaceholderText("(11) 99999-9999")
        plano = QComboBox()
        plano.addItems(["1 mês", "3 meses"])
        observacoes = QTextEdit()
        observacoes.setMaximumHeight(100)
        
        layout.addRow("Nome:", nome)
        layout.addRow("Número:", numero)
        layout.addRow("Plano:", plano)
        layout.addRow("Observações:", observacoes)
        
        btn_salvar = QPushButton("Salvar")
        btn_salvar.clicked.connect(lambda: self.salvar_cliente(dialog, nome.text(), numero.text(), plano.currentText(), observacoes.toPlainText()))
        layout.addWidget(btn_salvar)
        
        dialog.exec_()
    
    def salvar_cliente(self, dialog, nome, numero, plano, observacoes):
        """Salva novo cliente no banco"""
        if not nome or not numero:
            QMessageBox.warning(self, "Erro", "Nome e número são obrigatórios!")
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        data_pagamento = datetime.now().date()
        if plano == "1 mês":
            vencimento = data_pagamento + timedelta(days=30)
        else:
            vencimento = data_pagamento + timedelta(days=90)
        
        cursor.execute('''
            INSERT INTO clientes (nome, numero, status, plano, data_pagamento, data_vencimento, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (nome, numero, 'pago', plano.replace(' ', '_'), data_pagamento, vencimento, observacoes))
        
        conn.commit()
        conn.close()
        dialog.close()
        self.load_clientes()
    
    def load_clientes(self):
        """Carrega clientes na tabela"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes ORDER BY nome")
        self.clientes = cursor.fetchall()
        conn.close()
        
        self.tabela_clientes.setRowCount(len(self.clientes))
        for row, cliente in enumerate(self.clientes):
            self.tabela_clientes.setItem(row, 0, QTableWidgetItem(cliente[1]))  # nome
            self.tabela_clientes.setItem(row, 1, QTableWidgetItem(cliente[2]))  # numero
            self.tabela_clientes.setItem(row, 2, QTableWidgetItem(cliente[3].replace('_', ' ').title()))  # status
            self.tabela_clientes.setItem(row, 3, QTableWidgetItem(cliente[4].replace('_', ' ')))  # plano
            self.tabela_clientes.setItem(row, 4, QTableWidgetItem(str(cliente[6]) if cliente[6] else ''))  # vencimento
            self.tabela_clientes.setItem(row, 5, QTableWidgetItem(str(cliente[8]) if cliente[8] else ''))  # ultima msg
            self.tabela_clientes.setItem(row, 6, QTableWidgetItem("📤 ✏️ 💰"))  # ações
        
        self.atualizar_relatorios()
    
    def filtrar_clientes(self):
        """Filtra clientes na tabela"""
        status = self.filter_status.currentText().lower().replace(' ', '_')
        texto = self.search_input.text().lower()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM clientes WHERE 1=1"
        params = []
        
        if status != "todos":
            query += " AND status = ?"
            params.append(status)
        
        if texto:
            query += " AND (nome LIKE ? OR numero LIKE ?)"
            params.extend([f'%{texto}%', f'%{texto}%'])
        
        query += " ORDER BY nome"
        cursor.execute(query, params)
        filtered = cursor.fetchall()
        conn.close()
        
        self.tabela_clientes.setRowCount(len(filtered))
        for row, cliente in enumerate(filtered):
            self.tabela_clientes.setItem(row, 0, QTableWidgetItem(cliente[1]))
            self.tabela_clientes.setItem(row, 1, QTableWidgetItem(cliente[2]))
            self.tabela_clientes.setItem(row, 2, QTableWidgetItem(cliente[3].replace('_', ' ').title()))
            self.tabela_clientes.setItem(row, 3, QTableWidgetItem(cliente[4].replace('_', ' ')))
            self.tabela_clientes.setItem(row, 4, QTableWidgetItem(str(cliente[6]) if cliente[6] else ''))
            self.tabela_clientes.setItem(row, 5, QTableWidgetItem(str(cliente[8]) if cliente[8] else ''))
            self.tabela_clientes.setItem(row, 6, QTableWidgetItem("📤 ✏️ 💰"))
    
    def conectar_whatsapp(self):
        """Simula conexão WhatsApp Web (use pywhatkit ou whatsapp-web.js para produção)"""
        # Placeholder para integração real com WhatsApp
        self.whatsapp_status.setText("✅ WhatsApp Conectado")
        self.whatsapp_status.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; background: #e8f5e8; border-radius: 8px;")
        QMessageBox.information(self, "Sucesso", "WhatsApp conectado! (Simulação - integre com API real)")
    
    def toggle_auto_reply(self, state):
        """Ativa/desativa auto reply"""
        self.auto_reply_active = state == Qt.Checked
        status = "ATIVO" if self.auto_reply_active else "INATIVO"
        self.log_auto.append(f"[{datetime.now().strftime('%H:%M:%S')}] Auto Reply {status}")
    
    def atualizar_relatorios(self):
        """Atualiza estatísticas"""
        total = len(self.clientes)
        devendo = len([c for c in self.clientes if c[3] == 'devendo'])
        ativo = len([c for c in self.clientes if c[3] == 'em_atendimento'])
        
        self.lbl_total.setText(f"Total: {total}")
        self.lbl_devendo.setText(f"Devendo: {devendo}")
        self.lbl_ativo.setText(f"Ativo: {ativo}")
        self.lbl_vencendo.setText("Vencendo: 0")  # Implementar lógica
    
    def exportar_relatorio(self):
        """Exporta relatório"""
        file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Relatório", "relatorio_clientes.csv", "CSV (*.csv)")
        if file_path:
            with open(file_path, 'w') as f:
                f.write("Nome,Número,Status,Plano,Vencimento\n")
                for cliente in self.clientes:
                    f.write(f"{cliente[1]},{cliente[2]},{cliente[3]},{cliente[4]},{cliente[6]}\n")
            QMessageBox.information(self, "Sucesso", "Relatório exportado!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WhatsAppManager()
    window.show()
    sys.exit(app.exec_())
