import sys
import re
import ast
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTextEdit, QVBoxLayout, 
                             QHBoxLayout, QWidget, QPushButton, QLabel, QComboBox, 
                             QSplitter, QFrame, QScrollArea, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QFontMetrics

class CodeHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []
        
        # Definição de regras de destaque para Python
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(Qt.GlobalColor.darkBlue)
        keyword_format.setFontWeight(QFont.Weight.Bold.value)
        
        keywords = ["and", "as", "assert", "break", "class", "continue", "def", 
                   "del", "elif", "else", "except", "finally", "for", "from", 
                   "global", "if", "import", "in", "is", "lambda", "nonlocal", 
                   "not", "or", "pass", "raise", "return", "try", "while", "with", "yield"]
        
        for word in keywords:
            pattern = re.compile(rf'\b{word}\b')
            self.highlighting_rules.append((pattern, keyword_format))
    
    def highlightBlock(self, text):
        for pattern, format_obj in self.highlighting_rules:
            for match in pattern.finditer(text):
                start = match.start()
                length = match.end() - match.start()
                self.setFormat(start, length, format_obj)

class CodeAnalyzer(QThread):
    code_improved = pyqtSignal(str)
    progress_updated = pyqtSignal(str)
    
    def __init__(self, original_code, improvement_type):
        super().__init__()
        self.original_code = original_code
        self.improvement_type = improvement_type
        self._stop = False
    
    def run(self):
        if self._stop:
            return
            
        try:
            self.progress_updated.emit("Analisando código original...")
            improved_code = self.improve_code(self.original_code, self.improvement_type)
            self.code_improved.emit(improved_code)
        except Exception as e:
            self.code_improved.emit(f"Erro na análise: {str(e)}")
    
    def improve_code(self, code, improvement_type):
        lines = code.split('\n')
        improved_lines = lines.copy()
        
        self.progress_updated.emit("Aplicando melhorias...")
        
        # Melhorias específicas por tipo
        if improvement_type == "performance":
            improved_lines = self.optimize_performance(improved_lines)
        elif improvement_type == "readability":
            improved_lines = self.improve_readability(improved_lines)
        elif improvement_type == "security":
            improved_lines = self.improve_security(improved_lines)
        elif improvement_type == "style":
            improved_lines = self.improve_style(improved_lines)
        elif improvement_type == "all":
            improved_lines = self.optimize_performance(improved_lines)
            improved_lines = self.improve_readability(improved_lines)
            improved_lines = self.improve_security(improved_lines)
            improved_lines = self.improve_style(improved_lines)
        
        return '\n'.join(improved_lines)
    
    def optimize_performance(self, lines):
        # Otimizações de performance mantendo estrutura
        for i, line in enumerate(lines):
            # Substituir append em loop por list comprehension quando possível
            if 'for' in line and '.append(' in line:
                lines[i] = self.optimize_list_comprehension(line)
            # Evitar chamadas repetidas de funções
            lines[i] = re.sub(r'len\(([^)]+)\)', r'__len_cache__\1', line)
        return lines
    
    def improve_readability(self, lines):
        for i, line in enumerate(lines):
            # Adicionar espaços em operadores
            line = re.sub(r'(\w)([+\-*/])(\w)', r'\1 \2 \3', line)
            # Quebrar linhas longas
            if len(line) > 88:
                lines[i] = self.wrap_long_line(line)
            lines[i] = line
        return lines
    
    def improve_security(self, lines):
        for i, line in enumerate(lines):
            # Sanitizar inputs
            if 'input(' in line:
                lines[i] = line.replace('input(', 'input().strip() or ')
            # Usar with para arquivos
            if 'open(' in line and 'as f:' not in line:
                lines[i] = self.add_context_manager(line)
        return lines
    
    def improve_style(self, lines):
        for i, line in enumerate(lines):
            # PEP8: 4 espaços, sem tabs
            lines[i] = line.replace('\t', '    ')
            # Espaços após :
            lines[i] = re.sub(r':([^ ])', r': \1', lines[i])
            # Espaços em torno de = para defaults
            lines[i] = re.sub(r'(\w)=([^ ])', r'\1= \2', lines[i])
        return lines
    
    def optimize_list_comprehension(self, line):
        # Exemplo simples - em produção seria mais sofisticado
        return line  # Placeholder para lógica mais complexa
    
    def wrap_long_line(self, line):
        # Placeholder para quebra inteligente de linha
        return line
    
    def add_context_manager(self, line):
        return line  # Placeholder

class CodeImprover(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.highlighter_original = None
        self.highlighter_improved = None
        self.analyzer_thread = None
        
    def init_ui(self):
        self.setWindowTitle("Code Improver Pro - Otimizador de Código")
        self.setGeometry(100, 100, 1400, 900)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Header
        header = QFrame()
        header.setFrameStyle(QFrame.Shape.Box.value)
        header_layout = QHBoxLayout(header)
        
        title = QLabel("🤖 Code Improver Pro")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold.value))
        title.setStyleSheet("color: #2c3e50; padding: 10px;")
        
        self.improvement_type = QComboBox()
        self.improvement_type.addItems([
            "all - Completo", 
            "performance - Performance", 
            "readability - Legibilidade", 
            "security - Segurança", 
            "style - Estilo PEP8"
        ])
        self.improvement_type.setStyleSheet("""
            QComboBox {
                padding: 8px 12px; 
                font-size: 12px; 
                border: 2px solid #3498db; 
                border-radius: 6px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ecf0f1, stop:1 #ffffff);
            }
            QComboBox::drop-down { 
                border: none; 
                width: 30px; 
            }
        """)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(QLabel("Tipo de melhoria:"))
        header_layout.addWidget(self.improvement_type)
        header_layout.addStretch()
        
        main_layout.addWidget(header)
        
        # Splitter principal
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet("QSplitter::handle { background: #bdc3c7; }")
        
        # Área original
        original_frame = QFrame()
        original_layout = QVBoxLayout(original_frame)
        original_layout.addWidget(QLabel("📝 Código Original"))
        self.original_code = QTextEdit()
        self.original_code.setFont(QFont("Consolas", 11))
        self.original_code.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e74c3c;
                border-radius: 8px;
                padding: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #fdf2e9, stop:1 #fafafa);
            }
        """)
        self.original_code.setPlaceholderText("Cole aqui seu código Python para análise...")
        original_layout.addWidget(self.original_code)
        
        # Área melhorada
        improved_frame = QFrame()
        improved_layout = QVBoxLayout(improved_frame)
        improved_layout.addWidget(QLabel("✨ Código Melhorado"))
        self.improved_code = QTextEdit()
        self.improved_code.setFont(QFont("Consolas", 11))
        self.improved_code.setStyleSheet("""
            QTextEdit {
                border: 2px solid #27ae60;
                border-radius: 8px;
                padding: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #e8f8f5, stop:1 #f9f9f9);
            }
        """)
        self.improved_code.setPlaceholderText("O código melhorado aparecerá aqui...")
        self.improved_code.setReadOnly(True)
        improved_layout.addWidget(self.improved_code)
        
        splitter.addWidget(original_frame)
        splitter.addWidget(improved_frame)
        splitter.setSizes([450, 450])
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(splitter)
        scroll_area.setWidgetResizable(True)
        
        main_layout.addWidget(scroll_area)
        
        # Botões
        button_layout = QHBoxLayout()
        
        self.analyze_btn = QPushButton("🚀 Analisar e Melhorar")
        self.analyze_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold.value))
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #5dade2, stop:1 #3498db);
            }
            QPushButton:pressed {
                background: #2c82c9;
            }
            QPushButton:disabled {
                background: #bdc3c7;
            }
        """)
        self.analyze_btn.clicked.connect(self.analyze_code)
        
        self.copy_btn = QPushButton("📋 Copiar Código Melhorado")
        self.copy_btn.clicked.connect(self.copy_improved_code)
        
        self.clear_btn = QPushButton("🗑️ Limpar Tudo")
        self.clear_btn.clicked.connect(self.clear_all)
        
        button_layout.addStretch()
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.copy_btn)
        button_layout.addWidget(self.analyze_btn)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Pronto para analisar código")
        
        # Aplicar highlight
        self.apply_highlighting()
    
    def apply_highlighting(self):
        self.highlighter_original = CodeHighlighter(self.original_code.document())
        self.highlighter_improved = CodeHighlighter(self.improved_code.document())
    
    def analyze_code(self):
        original_text = self.original_code.toPlainText().strip()
        if not original_text:
            QMessageBox.warning(self, "Aviso", "Por favor, cole um código para analisar!")
            return
        
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.setText("🔄 Analisando...")
        self.status_bar.showMessage("Analisando código...")
        
        # Parar thread anterior se existir
        if self.analyzer_thread and self.analyzer_thread.isRunning():
            self.analyzer_thread._stop = True
            self.analyzer_thread.wait()
        
        improvement_type = self.improvement_type.currentText().split(" - ")[0].lower()
        self.analyzer_thread = CodeAnalyzer(original_text, improvement_type)
        self.analyzer_thread.code_improved.connect(self.on_code_improved)
        self.analyzer_thread.progress_updated.connect(self.on_progress_updated)
        self.analyzer_thread.finished.connect(self.on_analysis_finished)
        self.analyzer_thread.start()
    
    def on_progress_updated(self, message):
        self.status_bar.showMessage(message)
    
    def on_code_improved(self, improved_code):
        self.improved_code.setPlainText(improved_code)
    
    def on_analysis_finished(self):
        self.analyze_btn.setEnabled(True)
        self.analyze_btn.setText("🚀 Analisar e Melhorar")
        self.status_bar.showMessage("Análise concluída!")
    
    def copy_improved_code(self):
        improved_text = self.improved_code.toPlainText()
        if improved_text:
            QApplication.clipboard().setText(improved_text)
            self.status_bar.showMessage("Código copiado para área de transferência!")
        else:
            QMessageBox.information(self, "Info", "Nenhum código melhorado para copiar!")
    
    def clear_all(self):
        self.original_code.clear()
        self.improved_code.clear()
        self.status_bar.showMessage("Tela limpa!")

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = CodeImprover()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
