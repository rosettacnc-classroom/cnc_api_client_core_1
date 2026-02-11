"""
| Elemento      | Colore          | Esempi                            |
| ------------- | --------------- | --------------------------------- |
| **Comandi G** | Rosso           | `G0`, `G1`, `G28`, `G81`, `G90`   |
| **Comandi M** | Rosa            | `M3`, `M5`, `M6`, `M30`, `M104`   |
| **Assi**      | Ciano grassetto | `X10.5`, `Y-20`, `Z5.0`, `E1.5`   |
| **Parametri** | Verde           | `F1500`, `S12000`, `P100`, `I5.0` |
| **Numeri**    | Viola           | coordinate, valori                |
| **Tool**      | Arancione       | `T1`, `T0`                        |
| **Commenti**  | Blu grigio      | `(commento)` o `; commento`       |
| **Variabili** | Giallo          | `#100`, `#<varname>`              |

Punti Importanti:

    - Garbage Collection:
        L'highlighter deve rimanere in memoria! Memorizzalo come attributo della classe (self.highlighter),
        non come variabile locale.

    - Document:
        Passa sempre editor.document(), non l'editor stesso.

    - Temi:
        Puoi cambiare i colori dell'highlighter modificando il dizionario self.colors prima di applicarlo.

    - Performance:
        Se il G-Code è molto lungo (>10k linee), considera l'uso di QPlainTextEdit invece di QTextEdit (più veloce).
"""
from PySide6.QtCore import QRegularExpression

from PySide6.QtGui import (
    QColor,
    QTextCharFormat,
    QFont,
    QSyntaxHighlighter
)

class GCodeHighlighter(QSyntaxHighlighter):
    """Highlighter riutilizzabile per G-Code."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Colori
        self.colors = {
            'g_command' : QColor('#FF5555'),
            'm_command' : QColor('#FF79C6'),
            'axis'      : QColor('#8BE9FD'),
            'parameter' : QColor('#50FA7B'),
            'number'    : QColor('#BD93F9'),
            'comment'   : QColor('#6272A4'),
            'tool'      : QColor('#FFB86C'),
            'macro'     : QColor('#F1FA8C'),
        }

        self.formats = {}
        for name, color in self.colors.items():
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            if name in ['g_command', 'm_command', 'axis']:
                fmt.setFontWeight(QFont.Weight.Bold)
            self.formats[name] = fmt

        self.setup_rules()

    def setup_rules(self):
        self.compiled_rules = []

        # G-commands
        self.add_rule(r'\b[Gg]\d+(\.\d+)?\b', 'g_command')
        # M-commands
        self.add_rule(r'\b[Mm]\d+(\.\d+)?\b', 'm_command')
        # Assi
        self.add_rule(r'\b[XYZExyzEABCabc](?=[+-]?\d*\.?\d+)', 'axis')
        # Parametri
        self.add_rule(r'\b[FfSsRrPpIiJjKkDdHh](?=[+-]?\d*\.?\d+|\d)', 'parameter')
        # Tool
        self.add_rule(r'\b[Tt](?=\d+)', 'tool')
        # Numeri
        self.add_rule(r'[+-]?\d+\.\d+|\b\d+\b', 'number')
        # Macros
        self.add_rule(r'#\d+|#<[^>]+>', 'macro')
        # Commenti
        self.add_rule(r'\([^)]*\)', 'comment')
        self.add_rule(r';.*$', 'comment')

    def add_rule(self, pattern, format_name):
        regex = QRegularExpression(pattern)
        self.compiled_rules.append((regex, format_name))

    def highlightBlock(self, text):
        # Commenti prima
        for regex in [QRegularExpression(r'\([^)]*\)'), QRegularExpression(r';.*$')]:
            match_iterator = regex.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(),
                             self.formats['comment'])

        # Altri token
        for regex, fmt_name in self.compiled_rules:
            if fmt_name == 'comment':
                continue
            match_iterator = regex.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                start = match.capturedStart()
                length = match.capturedLength()
                if self.format(start) != self.formats['comment']:
                    self.setFormat(start, length, self.formats[fmt_name])
