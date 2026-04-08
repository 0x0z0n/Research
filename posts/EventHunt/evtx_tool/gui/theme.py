"""
Modern Dark / Cyber theme for EventHawk GUI.

Aesthetic: SentinelOne / EDR style. Deep charcoal and black backgrounds,
high-contrast off-white text, vibrant purple primary accents, and neon threat indicators.
"""

# ── Colour constants (also used by main_window for per-cell colouring) ────────

COLORS = {
    # Backgrounds
    "bg_main":    "#121215",   # deep black/charcoal — main window
    "bg_panel":   "#1C1C21",   # slightly lighter — panels / sidebars
    "bg_header":  "#23232A",   # dark gray — header bars
    "bg_input":   "#18181C",   # pure dark — inputs
    "bg_hover":   "#2A2A35",   # purple-tinted dark gray hover
    "bg_alt_row": "#18181C",   # alternating table row

    # Borders / separators
    "border":       "#2D2D36", # subtle dark gray
    "border_focus": "#613DC1", # vibrant purple focus ring

    # Text
    "text":       "#E0E0E0",   # off-white
    "text_dim":   "#A0A0A0",   # medium gray
    "text_muted": "#6C6C77",   # dim gray (muted)

    # Accents
    "accent":          "#613DC1",  # vibrant purple
    "accent_hover":    "#724CDA",  # lighter purple
    "selected_bg":     "#2A1B54",  # dark muted purple selected
    "selected_border": "#613DC1",  # vibrant purple

    # Event levels
    "level_critical": "#FF453A",  # neon red
    "level_error":    "#FF453A",
    "level_warning":  "#FF9F0A",  # bright orange
    "level_info":     "#E0E0E0",  # off-white (same as main text)
    "level_verbose":  "#6C6C77",  # muted gray

    # Analysis
    "attack_badge":   "#613DC1",  # vibrant purple
    "ioc_found":      "#32D74B",  # neon green
    "chain_critical": "#FF453A",
    "chain_high":     "#FF9F0A",
    "chain_medium":   "#0A84FF",  # neon blue
    "chain_low":      "#A0A0A0",

    # ATT&CK tactic colours (adjusted for dark mode visibility)
    "ta_recon":      "#8E8E93",
    "ta_resource":   "#636366",
    "ta_initial":    "#FF453A",
    "ta_exec":       "#FF375F",
    "ta_persist":    "#FF9F0A",
    "ta_privesc":    "#FFD60A",
    "ta_defense":    "#BF5AF2",
    "ta_cred":       "#FF8A65",
    "ta_discovery":  "#0A84FF",
    "ta_lateral":    "#30D158",
    "ta_collect":    "#34C759",
    "ta_c2":         "#5E5CE6",
    "ta_exfil":      "#FF375F",
    "ta_impact":     "#FF453A",

    # Buttons
    "btn_bg":        "#23232A",
    "btn_hover":     "#2D2D36",
    "btn_pressed":   "#1C1C21",
    "btn_parse_bg":  "#613DC1",   # Vibrant Purple — Parse action hero button
    "btn_parse_hov": "#724CDA",
    "btn_stop_bg":   "#FF453A",   # Neon Red
    "btn_stop_hov":  "#FF6961",

    # Progress
    "progress_bg":   "#23232A",
    "progress_fill": "#613DC1",
    "progress_text": "#FFFFFF",
}

# ── Master QSS stylesheet ──────────────────────────────────────────────────────

DARK_QSS = """
/* ── Global ─────────────────────────────────────────── */
* {
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 9pt;
    color: #E0E0E0;
    outline: none;
}

QMainWindow, QDialog {
    background: #121215;
}

QWidget {
    background: #121215;
    color: #E0E0E0;
}

/* ── Scroll Areas ────────────────────────────────────── */
QScrollArea {
    border: none;
    background: #121215;
}
QScrollArea > QWidget > QWidget {
    background: #121215;
}

/* ── Labels ──────────────────────────────────────────── */
QLabel {
    background: transparent;
    color: #E0E0E0;
}
QLabel#sectionHeader {
    color: #A0A0A0;
    font-size: 8pt;
    font-weight: bold;
    letter-spacing: 1px;
    padding: 6px 0px 2px 0px;
    border-bottom: 1px solid #2D2D36;
}
QLabel#statsLabel {
    color: #A0A0A0;
    font-size: 8pt;
}
QLabel#countLabel {
    color: #613DC1;
    font-size: 8pt;
    font-weight: bold;
}

/* ── Radio Buttons ───────────────────────────────────── */
QRadioButton {
    background: transparent;
    color: #E0E0E0;
    spacing: 6px;
}
QRadioButton:checked {
    color: #724CDA;
    font-weight: bold;
}
QRadioButton:disabled { color: #6C6C77; }

QRadioButton::indicator {
    width: 14px;
    height: 14px;
    border-radius: 7px;
    border: 2px solid #6C6C77;
    background: #18181C;
}
QRadioButton::indicator:hover {
    border-color: #613DC1;
    background: #1C1C21;
}
QRadioButton::indicator:checked {
    border: 1px solid #724CDA;
    background: #724CDA;
}
QRadioButton::indicator:checked:hover {
    border-color: #613DC1;
    background: #613DC1;
}
QRadioButton::indicator:disabled {
    border-color: #2D2D36;
    background: #1C1C21;
}

/* ── GroupBox ────────────────────────────────────────── */
QGroupBox {
    border: none;
    border-top: 1px solid #2D2D36;
    margin-top: 8px;
    padding-top: 6px;
    background: transparent;
    color: #A0A0A0;
    font-size: 8pt;
    font-weight: bold;
    letter-spacing: 1px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 4px;
    color: #A0A0A0;
}

/* ── Buttons ─────────────────────────────────────────── */
QPushButton {
    background: #23232A;
    color: #E0E0E0;
    border: 1px solid #2D2D36;
    border-radius: 4px;
    padding: 4px 10px;
    min-height: 22px;
}
QPushButton:hover {
    background: #2D2D36;
    border-color: #6C6C77;
}
QPushButton:pressed {
    background: #1C1C21;
    border-color: #613DC1;
}
QPushButton:disabled {
    color: #6C6C77;
    border-color: #2D2D36;
    background: #18181C;
}

QPushButton#parseBtn {
    background: #613DC1;
    color: #ffffff;
    border: 1px solid #724CDA;
    border-radius: 4px;
    font-weight: bold;
    min-height: 28px;
    font-size: 9pt;
}
QPushButton#parseBtn:hover {
    background: #724CDA;
    border-color: #8D6EF0;
}
QPushButton#parseBtn:pressed {
    background: #4C2B9D;
}
QPushButton#parseBtn:disabled {
    background: #2D2D36;
    color: #6C6C77;
    border-color: #363642;
}

QPushButton#stopBtn {
    background: #23232A;
    color: #FF453A;
    border: 1px solid #991C14;
    border-radius: 4px;
    min-height: 24px;
}
QPushButton#stopBtn:hover {
    background: #4A1A17;
    border-color: #FF453A;
}
QPushButton#stopBtn:disabled {
    color: #6C6C77;
    border-color: #2D2D36;
    background: #18181C;
}

QPushButton#exportBtn {
    background: #23232A;
    color: #0A84FF;
    border: 1px solid #004C99;
    border-radius: 4px;
    min-height: 24px;
}
QPushButton#exportBtn:hover {
    background: #002B59;
    border-color: #0A84FF;
}
QPushButton#exportBtn:disabled {
    color: #6C6C77;
    border-color: #2D2D36;
    background: #18181C;
}

/* ── Line Edits / Inputs ─────────────────────────────── */
QLineEdit, QTextEdit {
    background: #18181C;
    color: #E0E0E0;
    border: 1px solid #2D2D36;
    border-radius: 4px;
    padding: 3px 6px;
    selection-background-color: #613DC1;
    selection-color: #ffffff;
}
QLineEdit:focus, QTextEdit:focus {
    border-color: #613DC1;
}
QLineEdit:disabled {
    color: #6C6C77;
    background: #1C1C21;
}
QLineEdit#filterBar {
    background: #1C1C21;
    border: 1px solid #2D2D36;
    border-radius: 4px;
    padding: 4px 8px;
    color: #E0E0E0;
    font-size: 9pt;
}
QLineEdit#filterBar:focus {
    border-color: #613DC1;
    background: #18181C;
}

/* ── ComboBox ────────────────────────────────────────── */
QComboBox {
    background: #1C1C21;
    color: #E0E0E0;
    border: 1px solid #2D2D36;
    border-radius: 4px;
    padding: 3px 6px;
    min-height: 22px;
}
QComboBox:focus, QComboBox:on {
    border-color: #613DC1;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #A0A0A0;
    width: 0;
    height: 0;
}
QComboBox QAbstractItemView {
    background: #18181C;
    border: 1px solid #2D2D36;
    selection-background-color: #2A1B54;
    selection-color: #E0E0E0;
    outline: none;
}

/* ── SpinBox / DateTimeEdit ──────────────────────────── */
QSpinBox, QDateTimeEdit {
    background: #1C1C21;
    color: #E0E0E0;
    border: 1px solid #2D2D36;
    border-radius: 4px;
    padding: 3px 6px;
    min-height: 22px;
}
QSpinBox:focus, QDateTimeEdit:focus {
    border-color: #613DC1;
}
QSpinBox::up-button, QSpinBox::down-button,
QDateTimeEdit::up-button, QDateTimeEdit::down-button {
    background: #23232A;
    border: none;
    width: 16px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDateTimeEdit::up-button:hover, QDateTimeEdit::down-button:hover {
    background: #2D2D36;
}
QDateTimeEdit::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid #2D2D36;
    background: #23232A;
}
QDateTimeEdit::drop-down:hover { background: #2D2D36; }
QDateTimeEdit::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #A0A0A0;
    width: 0; height: 0;
}

/* Calendar popup */
QCalendarWidget { background: #1C1C21; color: #E0E0E0; }
QCalendarWidget QAbstractItemView {
    background: #18181C;
    color: #E0E0E0;
    selection-background-color: #613DC1;
    selection-color: #ffffff;
    alternate-background-color: #121215;
    outline: none;
}
QCalendarWidget QAbstractItemView:enabled  { color: #E0E0E0; }
QCalendarWidget QAbstractItemView:disabled { color: #6C6C77; }
QCalendarWidget QWidget#qt_calendar_navigationbar {
    background: #23232A;
    min-height: 28px;
}
QCalendarWidget QToolButton {
    background: #23232A;
    color: #E0E0E0;
    border: none;
    padding: 4px 8px;
    font-weight: bold;
}
QCalendarWidget QToolButton:hover {
    background: #2D2D36;
    color: #613DC1;
}
QCalendarWidget QToolButton::menu-indicator { image: none; }
QCalendarWidget QSpinBox {
    background: #1C1C21;
    color: #E0E0E0;
    border: 1px solid #2D2D36;
    selection-background-color: #613DC1;
}

/* ── CheckBox ────────────────────────────────────────── */
QCheckBox {
    background: transparent;
    spacing: 6px;
    color: #E0E0E0;
}
QCheckBox::indicator {
    width: 13px;
    height: 13px;
    border: 1px solid #2D2D36;
    border-radius: 3px;
    background: #18181C;
}
QCheckBox::indicator:checked {
    background: #613DC1;
    border-color: #724CDA;
}
QCheckBox::indicator:checked:hover {
    background: #724CDA;
}
QCheckBox::indicator:hover {
    border-color: #6C6C77;
}
QCheckBox:disabled { color: #6C6C77; }

/* ── List Widget ─────────────────────────────────────── */
QListWidget {
    background: #18181C;
    border: 1px solid #2D2D36;
    border-radius: 4px;
    outline: none;
}
QListWidget::item {
    padding: 3px 6px;
    border: none;
}
QListWidget::item:selected {
    background: #2A1B54;
    color: #E0E0E0;
}
QListWidget::item:hover {
    background: #2A2A35;
}

/* ── Table View ──────────────────────────────────────── */
QTableView {
    background: #121215;
    alternate-background-color: #1C1C21;
    border: none;
    gridline-color: #2D2D36;
    selection-background-color: #2A1B54;
    selection-color: #E0E0E0;
    outline: none;
}
QTableView::item {
    padding: 2px 6px;
    border: none;
}
QTableView::item:selected {
    background: #2A1B54;
    color: #E0E0E0;
    border-left: 2px solid #613DC1;
}
QHeaderView {
    background: #23232A;
    border: none;
}
QHeaderView::section {
    background: #23232A;
    color: #A0A0A0;
    border: none;
    border-right: 1px solid #2D2D36;
    border-bottom: 1px solid #2D2D36;
    padding: 4px 6px;
    font-size: 8pt;
    font-weight: bold;
    letter-spacing: 0.5px;
}
QHeaderView::section:hover {
    background: #2D2D36;
    color: #E0E0E0;
}
QHeaderView::section:checked {
    background: #2A1B54;
}

/* ── Tree Widget ─────────────────────────────────────── */
QTreeWidget {
    background: #121215;
    alternate-background-color: #1C1C21;
    border: none;
    outline: none;
}
QTreeWidget::item {
    padding: 3px 4px;
}
QTreeWidget::item:selected {
    background: #2A1B54;
    color: #E0E0E0;
}
QTreeWidget::branch {
    background: transparent;
}
QTreeWidget::branch:closed:has-children {
    border-image: none;
    image: none;
}

/* ── Tab Widget ──────────────────────────────────────── */
QTabWidget::pane {
    border: none;
    border-top: 1px solid #2D2D36;
    background: #121215;
}
QTabBar {
    background: #1C1C21;
}
QTabBar::tab {
    background: #1C1C21;
    color: #A0A0A0;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 6px 14px;
    font-size: 9pt;
}
QTabBar::tab:selected {
    color: #E0E0E0;
    border-bottom: 2px solid #613DC1;
    background: #121215;
}
QTabBar::tab:hover {
    color: #E0E0E0;
    background: #2A2A35;
}

/* Default close-button slot — replaced per-tab by a custom QPushButton widget.
   Keep at zero size so no ghost button appears if a tab is added before the
   custom widget is set. */
QTabBar::close-button {
    width: 0;
    height: 0;
    image: none;
    border: none;
    background: transparent;
}

/* ── Splitter ────────────────────────────────────────── */
QSplitter::handle {
    background: #23232A;
}
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical   { height: 1px; }
QSplitter::handle:hover {
    background: #613DC1;
}

/* ── Scroll Bars ─────────────────────────────────────── */
QScrollBar:vertical {
    background: #121215;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #363642;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover { background: #613DC1; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #121215;
    height: 8px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #363642;
    border-radius: 4px;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover { background: #613DC1; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ── Progress Bar ────────────────────────────────────── */
QProgressBar {
    background: #23232A;
    border: none;
    border-radius: 2px;
    text-align: center;
    color: #E0E0E0;
    font-size: 8pt;
    max-height: 14px;
}
QProgressBar::chunk {
    background: #613DC1;
    border-radius: 2px;
}

/* ── Status Bar ──────────────────────────────────────── */
QStatusBar {
    background: #1C1C21;
    border-top: 1px solid #2D2D36;
    color: #A0A0A0;
    font-size: 8pt;
}
QStatusBar::item { border: none; }

/* ── Menu Bar ────────────────────────────────────────── */
QMenuBar {
    background: #1C1C21;
    color: #E0E0E0;
    border-bottom: 1px solid #2D2D36;
    padding: 2px 0;
}
QMenuBar::item {
    background: transparent;
    padding: 4px 10px;
}
QMenuBar::item:selected, QMenuBar::item:pressed {
    background: #2A2A35;
    color: #E0E0E0;
}
QMenu {
    background: #18181C;
    border: 1px solid #2D2D36;
    color: #E0E0E0;
}
QMenu::item {
    padding: 5px 24px 5px 12px;
}
QMenu::item:selected {
    background: #2A1B54;
    color: #E0E0E0;
}
QMenu::separator {
    height: 1px;
    background: #2D2D36;
    margin: 3px 0;
}

/* ── Text Browser (event detail) ─────────────────────── */
QTextBrowser {
    background: #18181C;
    color: #E0E0E0;
    border: none;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 9pt;
    selection-background-color: #613DC1;
}

/* ── Tool Tips ───────────────────────────────────────── */
QToolTip {
    background: #23232A;
    color: #E0E0E0;
    border: 1px solid #2D2D36;
    padding: 4px 8px;
}

/* ── Message Box ─────────────────────────────────────── */
QMessageBox { background: #1C1C21; }
QMessageBox QLabel { color: #E0E0E0; background: transparent; }
QMessageBox QPushButton { min-width: 70px; }

/* ── Input Dialog ────────────────────────────────────── */
QInputDialog { background: #1C1C21; }

/* ── Separator ───────────────────────────────────────── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    color: #2D2D36;
    background: #2D2D36;
}

/* ── Search term chip tags ───────────────────────────── */
QWidget#searchTagWidget {
    background: #2A1B54;
    border: 1px solid #613DC1;
    border-radius: 4px;
}
QLabel#searchTag {
    background: transparent;
    color: #E0E0E0;
    font-size: 8pt;
    padding: 0px 1px;
}
QPushButton#searchTagRemove {
    background: transparent;
    color: #A0A0A0;
    border: none;
    padding: 0px;
    font-size: 11pt;
    font-weight: bold;
    min-height: 14px;
    max-height: 16px;
    min-width: 14px;
    max-width: 16px;
}
QPushButton#searchTagRemove:hover {
    color: #FF453A;
    background: transparent;
}
"""


def apply_theme(app) -> None:
    """Apply the modern dark / cyber theme to a QApplication."""
    from PySide6.QtGui import QFont, QPalette, QColor

    app.setStyleSheet(DARK_QSS)

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor("#121215"))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor("#E0E0E0"))
    palette.setColor(QPalette.ColorRole.Base,            QColor("#18181C"))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor("#1C1C21"))
    palette.setColor(QPalette.ColorRole.Text,            QColor("#E0E0E0"))
    palette.setColor(QPalette.ColorRole.Button,          QColor("#23232A"))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor("#E0E0E0"))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor("#613DC1"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Link,            QColor("#613DC1"))
    palette.setColor(QPalette.ColorRole.ToolTipBase,     QColor("#23232A"))
    palette.setColor(QPalette.ColorRole.ToolTipText,     QColor("#E0E0E0"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#6C6C77"))
    app.setPalette(palette)

    font = QFont("Segoe UI", 9)
    app.setFont(font)