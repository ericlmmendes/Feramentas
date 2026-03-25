import sys
import re
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTextEdit, QVBoxLayout, 
                             QHBoxLayout, QWidget, QPushButton, QLabel, QComboBox, 
                             QSplitter, QFrame, QScrollArea, QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QFontMetrics, QColor

class MultiLanguageHighlighter(QSyntaxHighlighter):
    def __init__(self, document, language="python"):
        super().__init__(document)
        self.language = language
        self.rules = {}
        self.setup_rules()
    
    def setup_rules(self):
        # Python
        python_keywords = ["and", "as", "assert", "break", "class", "continue", "def", 
                          "del", "elif", "else", "except", "finally", "for", "from", 
                          "global", "if", "import", "in", "is", "lambda", "nonlocal", 
                          "not", "or", "pass", "raise", "return", "try", "while", "with", "yield"]
        
        self.rules = {
            'python': {
                'keywords': (python_keywords, QColor(100, 150, 255), True),
                'strings': (r'"[^"\\]*(\\[\s\S][^"\\]*)*"' + r"|'''[^'\\]*(\\[\s\S][^'\\]*)*?'''", QColor(0, 200, 0)),
                'comments': (r'#.*', QColor(120, 120, 120)),
                'functions': (r'\b[A-Za-z_][A-Za-z0-9_]*\s*(?=\()', QColor(255, 150, 0))
            },
            'html': {
                'tags': (r'</?[\w:\-]+(?:\s+[^\s>]+(?:=(?:"[^"]*"|\'[^\']*\'|[^\s>]+))?)*\s*/?>', QColor(200, 50, 50)),
                'attributes': (r'\b[\w-]+(?=\s*=)', QColor(100, 150, 255)),
                'comments': (r'<!--[\s\S]*?-->', QColor(120, 120, 120))
            },
            'css': {
                'properties': (r'[\w-]+\s*:', QColor(100, 150, 255)),
                'values': (r':\s*[^{};]+', QColor(0, 200, 0)),
                'selectors': (r'^[^\{]+(?=\{)', QColor(255, 150, 0))
            },
            'javascript': {
                'keywords': (["function", "var", "let", "const", "if", "else", "for", "while", "return"], QColor(100, 150, 255)),
                'strings': (r'"[^"\\]*(\\[\s\S][^"\\]*)*?"', QColor(0, 200, 0))
            },
            'json': {
                'keys': (r'"[a-zA-Z_][a-zA-Z0-9_]*"\s*:', QColor(100, 150, 255)),
                'strings': (r'"[^"\\]*(\\[\s\S][^"\\]*)*?"', QColor(0, 200, 0)),
                'numbers': (r'-?\d+(\.\d+)?([eE][+-]?\d+)?', QColor(255, 150, 0))
            }
        }
    
    def highlightBlock(self, text):
        rules = self.rules.get(self.language, self.rules['python'])
        
        for pattern_str, color in rules.values():
            if isinstance(pattern_str, list):  # keywords
                for word in pattern_str:
                    pattern = re.compile(rf'\b{re.escape(word)}\b')
                    format_obj = QTextCharFormat()
                    format_obj.setForeground(color)
                    for match in pattern.finditer(text):
                        self.setFormat(match.start(), match.end() - match.start(), format_obj)
            else:  # regex patterns
                pattern = re.compile(pattern_str)
                format_obj = QTextCharFormat()
                format_obj.setForeground(color)
                for match in pattern.finditer(text):
                    self.setFormat(match.start(), match.end() - match.start(), format_obj)

class UniversalCodeAnalyzer(QThread):
    code_improved = pyqtSignal(str)
    progress_updated = pyqtSignal(str, int)
    
    def __init__(self, original_code, language, improvement_type):
        super().__init__()
        self.original_code = original_code
        self.language = language.lower()
        self.improvement_type = improvement_type.lower()
    
    def run(self):
        try:
            self.progress_updated.emit("🔍 Detectando linguagem...", 10)
            improved_code = self.analyze_and_improve()
            self.code_improved.emit(improved_code)
        except Exception as e:
            self.code_improved.emit(f"❌ Erro: {str(e)}")
    
    def analyze_and_improve(self):
        lines = self.original_code.split('\n')
        improved_lines = lines.copy()
        
        improvements = {
            'performance': self.optimize_performance,
            'readability': self.improve_readability,
            'security': self.improve_security,
            'style': self.improve_style,
            'minify': self.minify_code,
            'all': self.improve_all
        }
        
        improvement_func = improvements.get(self.improvement_type, self.improve_all)
        self.progress_updated.emit("✨ Aplicando melhorias...", 50)
        
        improved_lines = improvement_func(improved_lines)
        return '\n'.join(improved_lines)
    
    def detect_language_patterns(self, lines):
        content = '\n'.join(lines)
        if '<!DOCTYPE html>' in content or '<html' in content:
            return 'html'
        elif '{' in content and '}' in content and ('px' in content or 'color' in content):
            return 'css'
        elif ('function' in content or '=>' in content) and ('{' in content):
            return 'javascript'
        elif content.strip().startswith('{') and content.strip().endswith('}'):
            try:
                json.loads(content)
                return 'json'
            except:
                pass
        return self.language
    
    def optimize_performance(self, lines):
        lang = self.detect_language_patterns(lines)
        if lang == 'python':
            for i, line in enumerate(lines):
                # List comprehensions
                lines[i] = re.sub(r'\[([^\]]+)\.append\(([^)]+)\)', r'[\2 for \1 in []]', line)
        elif lang == 'javascript':
            for i, line in enumerate(lines):
                lines[i] = re.sub(r'var\s+(\w+)\s*=\s*new\s+Array\(\)', r'const \1 = []', line)
        elif lang == 'css':
            # Remover comentários não essenciais
            lines = [re.sub(r'/\*.*?\*/', '', line, flags=re.DOTALL) for line in lines]
        return lines
    
    def improve_readability(self, lines):
        for i, line in enumerate(lines):
            # Espaçamento consistente
            line = re.sub(r'([{}();,])\s*', r'\1 ', line)
            line = re.sub(r'\s+([{}();,])', r' \1', line)
            
            # Quebrar linhas longas (>100 chars)
            if len(line) > 100:
                line = self.wrap_line(line)
            
            lines[i] = line
        return lines
    
    def improve_security(self, lines):
        lang = self.detect_language_patterns(lines)
        for i, line in enumerate(lines):
            if lang == 'html':
                # Escapar caracteres perigosos
                lines[i] = re.sub(r'(<script)|javascript:', r'<!-- BLOCKED: \1', line)
            elif lang == 'javascript':
                # Adicionar validação básica
                if 'innerHTML' in line:
                    lines[i] = line.replace('innerHTML', '.textContent')
            elif lang == 'python':
                if 'input(' in line:
                    lines[i] = line.replace('input(', 'input().strip()')
        return lines
    
    def improve_style(self, lines):
        lang = self.detect_language_patterns(lines)
        for i, line in enumerate(lines):
            if lang == 'css':
                # Organizar propriedades alfabeticamente seria ideal
                lines[i] = re.sub(r'\s*([a-z-]+):\s*([^;]+);?', r'  \1: \2;', line)
            elif lang == 'html':
                # Indentar tags
                if line.strip().startswith('</') or line.strip().endswith('>'):
                    lines[i] = line.replace('>', '>\n')
            elif lang == 'python':
                # PEP8 spacing
                lines[i] = re.sub(r':([^ ])', r': \1', line)
                lines[i] = re.sub(r'([a-zA-Z0-9_])=([a-zA-Z0-9_])', r'\1 = \2', line)
        return lines
    
    def minify_code(self, lines):
        lang = self.detect_language_patterns(lines)
        if lang == 'css':
            return [re.sub(r'\s+', ' ', re.sub(r'/\*.*?\*/', '', line)).strip() for line in lines]
        elif lang == 'javascript' or lang == 'html':
            return [re.sub(r'\s+', ' ', line).strip() for line in lines]
        return lines
    
    def improve_all(self, lines):
        lines = self.optimize_performance(lines)
        lines = self.improve_readability(lines)
        lines = self.improve_security(lines)
        lines = self.improve_style(lines)
        return lines
    
    def wrap_line(self, line):
        # Simple line wrapping
        if len(line) > 100:
            space_pos = line.rfind(' ', 80, 100)
            if space_pos > 0:
                return line[:space_pos] + '\n' + line[space_pos:].lstrip()
        return line

class CodeImproverPro(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_language = "python"
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("🚀 Code Improver Pro - Multi-Linguagem")
        self.setGeometry(100, 100, 1600, 1000)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Header com linguagem
        header = QFrame()
        header.setFrameStyle(QFrame.Shape.Box.value)
        header_layout = QHBoxLayout(header)
        
        title = QLabel("🎨 Code Improver Pro - Multi-Linguagem")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold.value))
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Python", "HTML", "CSS", "JavaScript", "JSON", "Auto"])
        self.language_combo.currentTextChanged.connect(self.on_language_changed)
        
        self.improvement_type = QComboBox()
        self.improvement_type.addItems([
            "all - Completa", "performance", "readability - Legibilidade", 
            "security - Segurança", "style - Estilo", "minify - Minificar"
        ])
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(QLabel("Linguagem:"))
        header_layout.addWidget(self.language_combo)
        header_layout.addWidget(QLabel("Melhoria:"))
        header_layout.addWidget(self.improvement_type)
        header_layout.addStretch()
        
        main_layout.addWidget(header)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Original
        original_frame = self.create_code_frame("📝 Código Original", "#e74c3c")
        self.original_code = original_frame['editor']
        
        # Improved
        improved_frame = self.create_code_frame("✨ Código Melhorado", "#27ae60")
        self.improved_code = improved_frame['editor']
        self.improved_code.setReadOnly(True)
        
        splitter.addWidget(original_frame['frame'])
        splitter.addWidget(improved_frame['frame'])
        splitter.setSizes([500, 500])
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(splitter)
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)
        
        # Buttons
        self.create_buttons(main_layout)
        
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Pronto! Cole seu código e selecione a linguagem")
    
    def create_code_frame(self, title, border_color):
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.addWidget(QLabel(title))
        
        editor = QTextEdit()
        editor.setFont(QFont("Consolas", 11))
        editor.setStyleSheet(f"""
            QTextEdit {{
                border: 2px solid {border_color};
                border-radius: 8px;
                padding: 15px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #fff5f5, stop:1 #fafafa);
            }}
        """)
        layout.addWidget(editor)
        
        return {'frame': frame, 'editor': editor}
    
    def create_buttons(self, main_layout):
        button_layout = QHBoxLayout()
        
        self.analyze_btn = QPushButton("🚀 ANALISAR & MELHORAR")
        self.analyze_btn.clicked.connect(self.analyze_code)
        
        self.copy_btn = QPushButton("📋 COPIAR MELHORADO")
        self.copy_btn.clicked.connect(self.copy_improved_code)
        
        self.clear_btn = QPushButton("🗑️ LIMPAR")
        self.clear_btn.clicked.connect(self.clear_all)
        
        self.compare_btn = QPushButton("🔍 COMPARAR")
        self.compare_btn.clicked.connect(self.compare_codes)
        
        for btn in [self.analyze_btn, self.copy_btn, self.clear_btn, self.compare_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #3498db, stop:1 #2980b9);
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover { background: #5dade2; }
            """)
        
        button_layout.addStretch()
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.compare_btn)
        button_layout.addWidget(self.copy_btn)
        button_layout.addWidget(self.analyze_btn)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
    
    def on_language_changed(self, lang):
        self.current_language = lang.lower()
        self.apply_highlighting()
    
    def apply_highlighting(self):
        lang_map = {
            "python": "python", "html": "html", "css": "css", 
            "javascript": "javascript", "json": "json", "auto": "python"
        }
        lang = lang_map.get(self.current_language, "python")
        
        if self.original_code:
            old_highlighter = self.original_code.document().findChild(QSyntaxHighlighter)
            if old_highlighter:
                old_highlighter.setDocument(None)
            self.highlighter_original = MultiLanguageHighlighter(self.original_code.document(), lang)
        
        if self.improved_code:
            old_highlighter = self.improved_code.document().findChild(QSyntaxHighlighter)
            if old_highlighter:
                old_highlighter.setDocument(None)
            self.highlighter_improved = MultiLanguageHighlighter(self.improved_code.document(), lang)
    
    def analyze_code(self):
        code = self.original_code.toPlainText().strip()
        if not code:
            QMessageBox.warning(self, "Aviso", "Cole um código primeiro!")
            return
        
        self.analyze_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        lang = "auto" if self.language_combo.currentText() == "Auto" else self.current_language
        improvement = self.improvement_type.currentText().split(" - ")[0].lower()
        
        self.analyzer = UniversalCodeAnalyzer(code, lang, improvement)
        self.analyzer.code_improved.connect(self.on_improved)
        self.analyzer.progress_updated.connect(self.on_progress)
        self.analyzer.finished.connect(self.on_finished)
        self.analyzer.start()
    
    def on_progress(self, message, value):
        self.progress_bar.setValue(value)
        self.status_bar.showMessage(message)
    
    def on_improved(self, code):
        self.improved_code.setPlainText(code)
    
    def on_finished(self):
        self.analyze_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("✅ Análise concluída!")
    
    def copy_improved_code(self):
        text = self.improved_code.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.status_bar.showMessage("📋 Copiado!")
    
    def clear_all(self):
        self.original_code.clear()
        self.improved_code.clear()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
    
    def compare_codes(self):
        # Simple diff simulation
        orig = self.original_code.toPlainText()
        imp = self.improved_code.toPlainText()
        if orig and imp:
            diff_lines = []
            for i, (o, n) in enumerate(zip(orig.split('\n'), imp.split('\n'))):
                if o.strip() != n.strip():
                    diff_lines.append(f"L{i+1}: {o[:50]}... → {n[:50]}...")
            QMessageBox.information(self, "Diferenças", "\n".join(diff_lines[:10]))

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = CodeImproverPro()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
