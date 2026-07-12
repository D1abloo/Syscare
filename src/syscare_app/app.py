from __future__ import annotations

import sys
import webbrowser
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QSystemTrayIcon,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from . import __app_name__, __version__
from .archives import compress_folder, extract_archive
from .maintenance import Issue, MaintenanceItem, maintenance_items, run_maintenance, scan_invalid_entries
from .packages import PackageManager, available_managers, install, list_installed, search, uninstall
from .recovery import RecoverableFile, recover_file, scan_recoverable
from .styles import APP_QSS
from .system import (
    AppEntry,
    CleanupReport,
    cleanup_targets,
    delete_target,
    format_bytes,
    list_installed_apps,
    performance_snapshot,
    scan_target,
    temperature_snapshot,
    uninstall_app,
)
from .updater import check_updates, install_git_update


ROOT = Path(__file__).resolve().parents[2]


class TaskThread(QThread):
    done = Signal(object)
    failed = Signal(str)

    def __init__(self, fn: Callable, *args):
        super().__init__()
        self.fn = fn
        self.args = args

    def run(self) -> None:
        try:
            self.done.emit(self.fn(*self.args))
        except Exception as exc:
            self.failed.emit(str(exc))


def make_label(text: str, object_name: str = "", muted: bool = False) -> QLabel:
    label = QLabel(text)
    if object_name:
        label.setObjectName(object_name)
    if muted:
        label.setProperty("muted", True)
    label.setWordWrap(True)
    return label


def make_button(text: str, primary: bool = False, danger: bool = False) -> QPushButton:
    button = QPushButton(text)
    if primary:
        button.setProperty("primary", True)
    if danger:
        button.setProperty("danger", True)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    return button


def card(title: str, subtitle: str = "") -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setProperty("card", True)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(8)
    layout.addWidget(make_label(title, muted=False))
    if subtitle:
        layout.addWidget(make_label(subtitle, muted=True))
    return frame, layout


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{__app_name__} {__version__}")
        self.icon_path = Path(__file__).with_name("assets") / "app_icon.svg"
        self.app_icon = QIcon(str(self.icon_path))
        self.setWindowIcon(self.app_icon)
        self.resize(1280, 820)
        self.threads: list[TaskThread] = []
        self._allow_close = False
        self._tray_notice_shown = False
        self.targets = cleanup_targets()
        self.cleanup_rows: dict[str, int] = {}
        self.cleanup_reports: dict[str, CleanupReport] = {}
        self.installed_apps: list[AppEntry] = []
        self.managers = available_managers()
        self.maintenance_items = maintenance_items()
        self.recoverable_files: list[RecoverableFile] = []

        self.root = QWidget()
        self.root.setObjectName("Root")
        self.setCentralWidget(self.root)
        root_layout = QVBoxLayout(self.root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_header())
        self.stack = QStackedWidget()
        root_layout.addWidget(self.stack, 1)

        self.dashboard_page = self._build_dashboard_page()
        self.clean_page = self._build_clean_page()
        self.maintenance_page = self._build_maintenance_page()
        self.recovery_page = self._build_recovery_page()
        self.apps_page = self._build_apps_page()
        self.archive_page = self._build_archive_page()
        self.help_page = self._build_help_page()

        for page in (
            self.dashboard_page,
            self.clean_page,
            self.maintenance_page,
            self.recovery_page,
            self.apps_page,
            self.archive_page,
            self.help_page,
        ):
            self.stack.addWidget(page)

        self._switch_page(0)
        self._refresh_performance()
        self.metric_timer = QTimer(self)
        self.metric_timer.timeout.connect(self._refresh_performance)
        self.metric_timer.start(2500)
        self._setup_tray()

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("Header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(22, 14, 22, 14)
        layout.setSpacing(14)

        brand_row = QHBoxLayout()
        logo = QLabel("S")
        logo.setObjectName("LogoMark")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFixedSize(40, 40)
        brand_text = QVBoxLayout()
        brand_text.setSpacing(1)
        brand_text.addWidget(make_label("SysCare", "AppTitle"))
        brand_text.addWidget(make_label("Linux y macOS", muted=True))
        brand_row.addWidget(logo)
        brand_row.addLayout(brand_text)
        layout.addLayout(brand_row)
        layout.addSpacing(12)

        self.nav_buttons: list[QPushButton] = []
        for index, text in enumerate(("Panel", "Limpieza", "Optimizar", "Recuperar", "Aplicaciones", "Archivos", "Ayuda")):
            button = QPushButton(text)
            button.setProperty("nav", True)
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked=False, i=index: self._switch_page(i))
            self.nav_buttons.append(button)
            layout.addWidget(button)

        layout.addStretch(1)
        self.header_metric = make_label("Memoria -- · Temp --", muted=True)
        self.header_metric.setObjectName("HeaderMetric")
        self.header_metric.setWordWrap(False)
        self.header_metric.setMinimumWidth(260)
        layout.addWidget(self.header_metric)
        version = make_label(f"v{__version__}", muted=True)
        layout.addWidget(version)
        return header

    def _page_shell(self, title: str, subtitle: str) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)
        layout.addWidget(make_label(title, "PageTitle"))
        layout.addWidget(make_label(subtitle, muted=True))
        return page, layout

    def start_open_animation(self) -> None:
        self.setWindowOpacity(0.0)
        self.open_animation = QPropertyAnimation(self, b"windowOpacity", self)
        self.open_animation.setDuration(420)
        self.open_animation.setStartValue(0.0)
        self.open_animation.setEndValue(1.0)
        self.open_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.open_animation.start()

    def _setup_tray(self) -> None:
        self.tray_icon = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray_menu = QMenu(self)
        self.tray_memory_action = QAction("Memoria: calculando...", self)
        self.tray_memory_action.setEnabled(False)
        self.tray_temp_action = QAction("Temperatura: calculando...", self)
        self.tray_temp_action.setEnabled(False)
        show_action = QAction("Mostrar/Ocultar SysCare", self)
        show_action.triggered.connect(self._toggle_window)
        scan_action = QAction("Escanear limpieza", self)
        scan_action.triggered.connect(lambda: (self._show_window(), self._switch_page(1), self._scan_cleanup()))
        update_action = QAction("Buscar actualizaciones", self)
        update_action.triggered.connect(lambda: (self._show_window(), self._check_updates()))
        quit_action = QAction("Salir", self)
        quit_action.triggered.connect(self._quit_from_tray)

        self.tray_menu.addAction(self.tray_memory_action)
        self.tray_menu.addAction(self.tray_temp_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(show_action)
        self.tray_menu.addAction(scan_action)
        self.tray_menu.addAction(update_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(quit_action)

        self.tray_icon = QSystemTrayIcon(self.app_icon, self)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.setToolTip("SysCare: memoria y temperatura")
        self.tray_icon.activated.connect(self._tray_activated)
        self.tray_icon.show()

    def _tray_activated(self, reason) -> None:
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self._toggle_window()

    def _toggle_window(self) -> None:
        if self.isVisible() and not self.isMinimized():
            self.hide()
            return
        self._show_window()

    def _show_window(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def _quit_from_tray(self) -> None:
        self._allow_close = True
        QApplication.quit()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._allow_close or not getattr(self, "tray_icon", None) or not self.tray_icon.isVisible():
            event.accept()
            return
        self.hide()
        if not self._tray_notice_shown:
            self.tray_icon.showMessage(
                "SysCare sigue activo",
                "La app queda abierta en la barra superior o bandeja del sistema. Usa Salir para cerrarla.",
                QSystemTrayIcon.MessageIcon.Information,
                3500,
            )
            self._tray_notice_shown = True
        event.ignore()

    def _build_dashboard_page(self) -> QWidget:
        page, layout = self._page_shell("Panel del equipo", "Rendimiento, temperatura y estado general en tiempo real.")

        hero = QFrame()
        hero.setObjectName("Hero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(20, 18, 20, 18)
        hero_layout.setSpacing(18)
        hero_copy = QVBoxLayout()
        hero_copy.addWidget(make_label("Centro de mantenimiento", "HeroTitle"))
        hero_copy.addWidget(make_label("Limpieza, optimizacion, recuperacion y paquetes desde una sola interfaz.", muted=True))
        quick_row = QHBoxLayout()
        quick_scan = make_button("Escanear basura", primary=True)
        quick_scan.clicked.connect(lambda: (self._switch_page(1), self._scan_cleanup()))
        quick_opt = make_button("Buscar problemas")
        quick_opt.clicked.connect(lambda: (self._switch_page(2), self._scan_invalid_entries()))
        quick_recovery = make_button("Recuperar archivos")
        quick_recovery.clicked.connect(lambda: (self._switch_page(3), self._scan_recovery()))
        quick_row.addWidget(quick_scan)
        quick_row.addWidget(quick_opt)
        quick_row.addWidget(quick_recovery)
        quick_row.addStretch(1)
        hero_copy.addLayout(quick_row)
        hero_layout.addLayout(hero_copy, 1)
        self.health_score = QLabel("100")
        self.health_score.setObjectName("HealthScore")
        self.health_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.health_score.setFixedSize(96, 96)
        hero_layout.addWidget(self.health_score)
        layout.addWidget(hero)

        metrics = QGridLayout()
        metrics.setSpacing(14)
        self.cpu_bar, self.cpu_value, cpu_card = self._metric_card("CPU")
        self.memory_bar, self.memory_value, memory_card = self._metric_card("Memoria")
        self.disk_bar, self.disk_value, disk_card = self._metric_card("Disco")
        self.battery_label = make_label("Sin bateria detectada", muted=True)
        battery_card, battery_layout = card("Bateria")
        battery_layout.addStretch(1)
        battery_layout.addWidget(self.battery_label)
        metrics.addWidget(cpu_card, 0, 0)
        metrics.addWidget(memory_card, 0, 1)
        metrics.addWidget(disk_card, 0, 2)
        metrics.addWidget(battery_card, 0, 3)
        layout.addLayout(metrics)

        lower = QGridLayout()
        lower.setSpacing(14)
        temp_card, temp_layout = card("Temperaturas", "Lecturas expuestas por el sistema operativo.")
        self.temp_list = QListWidget()
        temp_layout.addWidget(self.temp_list)
        lower.addWidget(temp_card, 0, 0)

        update_card, update_layout = card("Actualizaciones", "Comprueba el repositorio o GitHub Releases configurado.")
        self.update_status = make_label("Pulsa buscar para comprobar si hay una version nueva.", muted=True)
        update_button = make_button("Buscar actualizaciones", primary=True)
        update_button.clicked.connect(self._check_updates)
        update_layout.addWidget(self.update_status)
        update_layout.addWidget(update_button)
        update_layout.addStretch(1)
        lower.addWidget(update_card, 0, 1)
        layout.addLayout(lower, 1)
        return page

    def _metric_card(self, title: str) -> tuple[QProgressBar, QLabel, QFrame]:
        frame, layout = card(title)
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(0)
        value = make_label("0%", muted=True)
        layout.addWidget(value)
        layout.addWidget(bar)
        return bar, value, frame

    def _build_clean_page(self) -> QWidget:
        page, layout = self._page_shell("Limpieza segura", "Escanea primero y decide que categorias limpiar.")
        actions = QHBoxLayout()
        scan_button = make_button("Escanear", primary=True)
        clean_button = make_button("Limpiar seleccion", danger=True)
        scan_button.clicked.connect(self._scan_cleanup)
        clean_button.clicked.connect(self._clean_selected)
        actions.addWidget(scan_button)
        actions.addWidget(clean_button)
        actions.addStretch(1)
        self.clean_status = make_label("Listo para escanear.", muted=True)
        actions.addWidget(self.clean_status)
        layout.addLayout(actions)

        self.clean_table = QTableWidget(0, 6)
        self.clean_table.setHorizontalHeaderLabels(("Usar", "Categoria", "Objetivo", "Tamano", "Items", "Notas"))
        self.clean_table.verticalHeader().setVisible(False)
        self.clean_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.clean_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.clean_table.setAlternatingRowColors(True)
        layout.addWidget(self.clean_table, 1)
        self._populate_cleanup_table()
        return page

    def _populate_cleanup_table(self) -> None:
        self.clean_table.setRowCount(0)
        self.cleanup_rows.clear()
        for target in self.targets:
            row = self.clean_table.rowCount()
            self.clean_table.insertRow(row)
            checkbox = QCheckBox()
            checkbox.setChecked(not target.risky)
            checkbox.setProperty("target_key", target.key)
            self.clean_table.setCellWidget(row, 0, checkbox)
            self.clean_table.setItem(row, 1, QTableWidgetItem(target.category))
            self.clean_table.setItem(row, 2, QTableWidgetItem(target.name))
            self.clean_table.setItem(row, 3, QTableWidgetItem("--"))
            self.clean_table.setItem(row, 4, QTableWidgetItem("--"))
            note = "Requiere atencion: " + target.description if target.risky else target.description
            self.clean_table.setItem(row, 5, QTableWidgetItem(note))
            self.cleanup_rows[target.key] = row

    def _build_maintenance_page(self) -> QWidget:
        page, layout = self._page_shell("Optimizar y mantener", "Tareas de rendimiento y busqueda de entradas invalidas equivalentes al registro.")
        grid = QGridLayout()
        grid.setSpacing(14)

        tasks_card, tasks_layout = card("Acciones de optimizacion", "Ejecuta tareas conocidas del sistema con confirmacion previa.")
        self.maintenance_table = QTableWidget(0, 5)
        self.maintenance_table.setHorizontalHeaderLabels(("Categoria", "Accion", "Riesgo", "Estado", "Detalle"))
        self.maintenance_table.verticalHeader().setVisible(False)
        self.maintenance_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.maintenance_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.maintenance_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.maintenance_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.maintenance_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.maintenance_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._populate_maintenance_table()
        task_actions = QHBoxLayout()
        run_task = make_button("Ejecutar accion", primary=True)
        run_task.clicked.connect(self._run_selected_maintenance)
        scan_issues = make_button("Buscar entradas invalidas")
        scan_issues.clicked.connect(self._scan_invalid_entries)
        task_actions.addWidget(run_task)
        task_actions.addWidget(scan_issues)
        task_actions.addStretch(1)
        tasks_layout.addLayout(task_actions)
        tasks_layout.addWidget(self.maintenance_table)
        grid.addWidget(tasks_card, 0, 0)

        issues_card, issues_layout = card("Problemas detectados", "Enlaces rotos, accesos .desktop invalidos, LaunchAgents obsoletos y archivos grandes.")
        self.issue_status = make_label("Pulsa buscar para analizar el usuario actual.", muted=True)
        self.issue_table = QTableWidget(0, 4)
        self.issue_table.setHorizontalHeaderLabels(("Tipo", "Ruta", "Tamano", "Detalle"))
        self.issue_table.verticalHeader().setVisible(False)
        self.issue_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.issue_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        issues_layout.addWidget(self.issue_status)
        issues_layout.addWidget(self.issue_table)
        grid.addWidget(issues_card, 0, 1)

        layout.addLayout(grid, 1)
        return page

    def _populate_maintenance_table(self) -> None:
        self.maintenance_table.setRowCount(0)
        for item in self.maintenance_items:
            row = self.maintenance_table.rowCount()
            self.maintenance_table.insertRow(row)
            values = (item.category, item.title, "Alto" if item.risky else "Bajo", "Disponible", item.description)
            for col, value in enumerate(values):
                table_item = QTableWidgetItem(value)
                table_item.setData(Qt.ItemDataRole.UserRole, item)
                self.maintenance_table.setItem(row, col, table_item)

    def _build_recovery_page(self) -> QWidget:
        page, layout = self._page_shell("Recuperar archivos borrados", "Busca elementos en la papelera y restauralos a su ruta original o a otra carpeta.")
        recovery_card, recovery_layout = card("Busqueda de recuperables", "Funciona con archivos que siguen presentes en la papelera del usuario.")
        top_row = QHBoxLayout()
        self.recovery_query = QLineEdit()
        self.recovery_query.setPlaceholderText("Filtrar por nombre...")
        scan_button = make_button("Buscar borrados", primary=True)
        scan_button.clicked.connect(self._scan_recovery)
        restore_button = make_button("Restaurar original")
        restore_button.clicked.connect(self._recover_selected_original)
        restore_to_button = make_button("Restaurar en...")
        restore_to_button.clicked.connect(self._recover_selected_to)
        top_row.addWidget(self.recovery_query, 1)
        top_row.addWidget(scan_button)
        top_row.addWidget(restore_button)
        top_row.addWidget(restore_to_button)
        recovery_layout.addLayout(top_row)

        self.recovery_status = make_label("Listo para buscar en la papelera.", muted=True)
        recovery_layout.addWidget(self.recovery_status)
        self.recovery_table = QTableWidget(0, 5)
        self.recovery_table.setHorizontalHeaderLabels(("Nombre", "Tamano", "Borrado", "Origen", "En papelera"))
        self.recovery_table.verticalHeader().setVisible(False)
        self.recovery_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.recovery_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.recovery_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.recovery_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        recovery_layout.addWidget(self.recovery_table, 1)
        layout.addWidget(recovery_card, 1)
        return page

    def _build_apps_page(self) -> QWidget:
        page, layout = self._page_shell("Aplicaciones", "Busca, instala y desinstala con los gestores disponibles.")
        grid = QGridLayout()
        grid.setSpacing(14)

        installed_card, installed_layout = card("Apps instaladas", "Apps graficas detectadas en el sistema.")
        search_row = QHBoxLayout()
        self.installed_filter = QLineEdit()
        self.installed_filter.setPlaceholderText("Filtrar aplicaciones...")
        self.installed_filter.textChanged.connect(self._filter_installed_apps)
        refresh = make_button("Actualizar")
        refresh.clicked.connect(self._load_installed_apps)
        uninstall_button = make_button("Desinstalar app", danger=True)
        uninstall_button.clicked.connect(self._uninstall_selected_app)
        search_row.addWidget(self.installed_filter, 1)
        search_row.addWidget(refresh)
        search_row.addWidget(uninstall_button)
        installed_layout.addLayout(search_row)
        self.installed_table = QTableWidget(0, 4)
        self.installed_table.setHorizontalHeaderLabels(("Nombre", "Origen", "ID", "Ruta"))
        self.installed_table.verticalHeader().setVisible(False)
        self.installed_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.installed_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.installed_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        installed_layout.addWidget(self.installed_table)
        grid.addWidget(installed_card, 0, 0)

        package_card, package_layout = card("Instalador de paquetes", "Usa Homebrew, apt, dnf, pacman, snap o flatpak si estan instalados.")
        manager_row = QHBoxLayout()
        self.manager_combo = QComboBox()
        for manager in self.managers:
            self.manager_combo.addItem(manager.name, manager.key)
        if not self.managers:
            self.manager_combo.addItem("Sin gestores detectados", "")
        self.package_query = QLineEdit()
        self.package_query.setPlaceholderText("Buscar paquete o escribir nombre exacto...")
        search_button = make_button("Buscar", primary=True)
        search_button.clicked.connect(self._search_packages)
        manager_row.addWidget(self.manager_combo)
        manager_row.addWidget(self.package_query, 1)
        manager_row.addWidget(search_button)
        package_layout.addLayout(manager_row)

        action_row = QHBoxLayout()
        self.package_name = QLineEdit()
        self.package_name.setPlaceholderText("Nombre exacto del paquete")
        install_button = make_button("Instalar", primary=True)
        install_button.clicked.connect(self._install_package)
        remove_button = make_button("Desinstalar paquete", danger=True)
        remove_button.clicked.connect(self._remove_package)
        list_button = make_button("Ver instalados")
        list_button.clicked.connect(self._list_packages)
        action_row.addWidget(self.package_name, 1)
        action_row.addWidget(install_button)
        action_row.addWidget(remove_button)
        action_row.addWidget(list_button)
        package_layout.addLayout(action_row)

        self.package_output = QTextEdit()
        self.package_output.setReadOnly(True)
        self.package_output.setPlaceholderText("Los resultados apareceran aqui.")
        package_layout.addWidget(self.package_output, 1)
        grid.addWidget(package_card, 0, 1)

        layout.addLayout(grid, 1)
        self._load_installed_apps()
        return page

    def _build_archive_page(self) -> QWidget:
        page, layout = self._page_shell("Archivos comprimidos", "Comprime carpetas y descomprime archivos soportados por Python.")
        grid = QGridLayout()
        grid.setSpacing(14)

        compress_card, compress_layout = card("Comprimir carpeta")
        self.compress_source = QLineEdit()
        self.compress_dest = QLineEdit()
        self.compress_format = QComboBox()
        self.compress_format.addItems(("zip", "gztar", "bztar", "xztar"))
        compress_layout.addLayout(self._path_row("Carpeta origen", self.compress_source, lambda: self._pick_directory(self.compress_source)))
        compress_layout.addLayout(self._path_row("Archivo destino", self.compress_dest, lambda: self._pick_save_file(self.compress_dest)))
        compress_layout.addWidget(self.compress_format)
        compress_button = make_button("Comprimir", primary=True)
        compress_button.clicked.connect(self._compress_folder)
        compress_layout.addWidget(compress_button)
        grid.addWidget(compress_card, 0, 0)

        extract_card, extract_layout = card("Descomprimir archivo")
        self.extract_source = QLineEdit()
        self.extract_dest = QLineEdit()
        extract_layout.addLayout(self._path_row("Archivo origen", self.extract_source, lambda: self._pick_open_file(self.extract_source)))
        extract_layout.addLayout(self._path_row("Carpeta destino", self.extract_dest, lambda: self._pick_directory(self.extract_dest)))
        extract_button = make_button("Descomprimir", primary=True)
        extract_button.clicked.connect(self._extract_archive)
        extract_layout.addWidget(extract_button)
        grid.addWidget(extract_card, 0, 1)

        layout.addLayout(grid)
        self.archive_status = make_label("Listo.", muted=True)
        layout.addWidget(self.archive_status)
        layout.addStretch(1)
        return page

    def _path_row(self, label: str, field: QLineEdit, action: Callable) -> QHBoxLayout:
        row = QHBoxLayout()
        field.setPlaceholderText(label)
        button = make_button("Elegir")
        button.clicked.connect(action)
        row.addWidget(field, 1)
        row.addWidget(button)
        return row

    def _build_help_page(self) -> QWidget:
        page, layout = self._page_shell("Ayuda", "Instalacion, lanzamiento y uso responsable.")
        update_card, update_layout = card("Estado de actualizaciones", "Comprueba si hay cambios nuevos en el repositorio configurado.")
        update_grid = QHBoxLayout()
        self.help_update_status = make_label(f"Version instalada: {__version__}. Estado: no comprobado.", muted=True)
        help_update_button = make_button("Comprobar ahora", primary=True)
        help_update_button.clicked.connect(self._check_updates)
        update_grid.addWidget(self.help_update_status, 1)
        update_grid.addWidget(help_update_button)
        update_layout.addLayout(update_grid)
        update_layout.addWidget(make_label("Si se instala una actualizacion, reinicia SysCare para cargar los nuevos cambios.", muted=True))
        layout.addWidget(update_card)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setMarkdown(
            """
## Instalacion

Linux:

- Ubuntu/Debian/Mint: `sudo apt install python3 python3-venv python3-pip`
- Fedora/RHEL: `sudo dnf install python3 python3-pip python3-virtualenv`
- Arch/Manjaro: `sudo pacman -S python python-pip python-virtualenv`
- openSUSE: `sudo zypper install python3 python3-pip python3-virtualenv`
- Despues ejecuta: `./scripts/install-linux.sh`

macOS 13, 14 y 15:

- Con Homebrew: `brew install python && ./scripts/install-macos.sh`
- Sin Homebrew: instala Python 3.10+ desde python.org y ejecuta `./scripts/install-dev.sh`

Lanzamiento: `syscare` o `./scripts/run.sh`

## Uso

- Escanea antes de limpiar. Las categorias de privacidad pueden cerrar sesiones.
- Optimizar incluye DNS, cache de fuentes, limpieza de paquetes y revision de entradas invalidas.
- Linux/macOS no tienen registro de Windows; SysCare revisa equivalentes como enlaces rotos, `.desktop` invalidos y LaunchAgents obsoletos.
- Recuperar busca archivos que aun estan en la papelera. No puede garantizar recuperacion forense de archivos eliminados permanentemente.
- En macOS, la desinstalacion mueve apps `.app` a la papelera.
- En Linux, instala y elimina paquetes desde el gestor detectado. Puede pedir permisos con `pkexec` o `sudo`.
- La compresion usa formatos `zip`, `gztar`, `bztar` y `xztar`.
- Las actualizaciones se consultan desde `SYSCARE_REPO_URL`, GitHub Releases o el remoto `origin` si ejecutas desde un clon Git.

## Seguridad

SysCare evita rutas del sistema y trabaja sobre carpetas del usuario o temporales conocidas. Revisa siempre las rutas y cierra navegadores antes de borrar cookies o caché.
            """.strip()
        )
        layout.addWidget(help_text, 1)
        return page

    def _switch_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons):
            button.setChecked(i == index)
        page = self.stack.currentWidget()
        effect = QGraphicsOpacityEffect(page)
        page.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(220)
        animation.setStartValue(0.55)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.finished.connect(lambda: page.setGraphicsEffect(None))
        animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    def _run_task(self, fn: Callable, on_done: Callable, *args) -> None:
        thread = TaskThread(fn, *args)
        thread.done.connect(on_done)
        thread.failed.connect(lambda message: QMessageBox.critical(self, "Error", message))
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        self.threads.append(thread)
        thread.start()

    def _cleanup_thread(self, thread: TaskThread) -> None:
        if thread in self.threads:
            self.threads.remove(thread)

    @Slot()
    def _refresh_performance(self) -> None:
        data = performance_snapshot()
        self.cpu_bar.setValue(int(data["cpu"]))
        self.cpu_value.setText(f"{data['cpu']:.0f}% de uso")
        self.memory_bar.setValue(int(data["memory_percent"]))
        self.memory_value.setText(f"{data['memory_percent']:.0f}% · {format_bytes(int(data['memory_used']))} / {format_bytes(int(data['memory_total']))}")
        self.disk_bar.setValue(int(data["disk_percent"]))
        self.disk_value.setText(f"{data['disk_percent']:.0f}% · {format_bytes(int(data['disk_used']))} / {format_bytes(int(data['disk_total']))}")
        battery = data["battery"]
        self.battery_label.setText(f"{battery:.0f}% disponible" if battery is not None else "Sin bateria detectada")
        score = max(0, 100 - int(data["cpu"] * 0.25) - int(data["memory_percent"] * 0.35) - int(data["disk_percent"] * 0.20))
        self.health_score.setText(str(score))
        self.health_score.setToolTip("Estimacion visual basada en CPU, memoria y disco.")

        temps = temperature_snapshot()
        temp_values = [value for _, value in temps if value is not None]
        temp_summary = f"{temp_values[0]:.1f} C" if temp_values else "N/D"
        memory_summary = f"{data['memory_percent']:.0f}% · {format_bytes(int(data['memory_used']))}"
        self.header_metric.setText(f"Memoria {memory_summary} · Temp {temp_summary}")
        if getattr(self, "tray_icon", None):
            self.tray_memory_action.setText(f"Memoria: {memory_summary} de {format_bytes(int(data['memory_total']))}")
            self.tray_temp_action.setText(f"Temperatura: {temp_summary}")
            self.tray_icon.setToolTip(f"SysCare\nMemoria: {memory_summary}\nTemperatura: {temp_summary}")

        self.temp_list.clear()
        if not temps:
            self.temp_list.addItem("No hay sensores de temperatura expuestos por el sistema.")
        for name, value in temps[:24]:
            self.temp_list.addItem(f"{name}: {value:.1f} C" if value is not None else f"{name}: N/D")

    def _scan_cleanup(self) -> None:
        self.clean_status.setText("Escaneando rutas...")
        self._run_task(lambda targets: [scan_target(target) for target in targets], self._scan_done, self.targets)

    def _scan_done(self, reports: list[CleanupReport]) -> None:
        total = 0
        for report in reports:
            self.cleanup_reports[report.target.key] = report
            row = self.cleanup_rows[report.target.key]
            self.clean_table.item(row, 3).setText(format_bytes(report.size))
            self.clean_table.item(row, 4).setText(str(report.items))
            if report.errors:
                self.clean_table.item(row, 5).setText(f"{report.target.description} · {len(report.errors)} avisos")
            total += report.size
        self.clean_status.setText(f"Escaneo completo: {format_bytes(total)} encontrados.")

    def _selected_targets(self) -> list:
        selected = []
        for target in self.targets:
            row = self.cleanup_rows[target.key]
            checkbox = self.clean_table.cellWidget(row, 0)
            if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                selected.append(target)
        return selected

    def _clean_selected(self) -> None:
        selected = self._selected_targets()
        if not selected:
            QMessageBox.information(self, "Limpieza", "Selecciona al menos una categoria.")
            return
        names = ", ".join(target.name for target in selected)
        answer = QMessageBox.question(
            self,
            "Confirmar limpieza",
            f"Se moveran a la papelera o eliminaran elementos de: {names}. Continuar?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.clean_status.setText("Limpiando seleccion...")
        self._run_task(lambda targets: [delete_target(target) for target in targets], self._clean_done, selected)

    def _clean_done(self, reports: list[CleanupReport]) -> None:
        total = sum(report.size for report in reports)
        errors = sum(len(report.errors) for report in reports)
        self.clean_status.setText(f"Limpieza terminada: {format_bytes(total)} procesados, {errors} avisos.")
        self._scan_cleanup()

    def _selected_maintenance(self) -> MaintenanceItem | None:
        row = self.maintenance_table.currentRow()
        if row < 0:
            return None
        item = self.maintenance_table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _run_selected_maintenance(self) -> None:
        item = self._selected_maintenance()
        if not item:
            QMessageBox.information(self, "Optimizar", "Selecciona una accion de mantenimiento.")
            return
        answer = QMessageBox.question(self, "Confirmar optimizacion", f"Ejecutar: {item.title}?\n\n{item.description}")
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.issue_status.setText(f"Ejecutando {item.title}...")
        self._run_task(run_maintenance, self._maintenance_done, item)

    def _maintenance_done(self, result: tuple[int, str]) -> None:
        code, output = result
        self.issue_status.setText(f"Accion terminada con codigo {code}.")
        QMessageBox.information(self, "Optimizar", output or f"Codigo: {code}")

    def _scan_invalid_entries(self) -> None:
        self.issue_status.setText("Analizando entradas invalidas y archivos pesados...")
        self._run_task(scan_invalid_entries, self._invalid_entries_done)

    def _invalid_entries_done(self, issues: list[Issue]) -> None:
        self.issue_table.setRowCount(0)
        for issue in issues:
            row = self.issue_table.rowCount()
            self.issue_table.insertRow(row)
            values = (issue.kind, issue.path, format_bytes(issue.size) if issue.size else "--", issue.detail)
            for col, value in enumerate(values):
                self.issue_table.setItem(row, col, QTableWidgetItem(value))
        self.issue_status.setText(f"Analisis completado: {len(issues)} elementos encontrados.")

    def _scan_recovery(self) -> None:
        self.recovery_status.setText("Buscando archivos borrados en la papelera...")
        self._run_task(scan_recoverable, self._recovery_done, self.recovery_query.text())

    def _recovery_done(self, files: list[RecoverableFile]) -> None:
        self.recoverable_files = files
        self.recovery_table.setRowCount(0)
        for file in files:
            row = self.recovery_table.rowCount()
            self.recovery_table.insertRow(row)
            values = (file.name, format_bytes(file.size), file.deleted_at or "--", file.original_path or "--", file.trash_path)
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, file)
                self.recovery_table.setItem(row, col, item)
        self.recovery_status.setText(f"Encontrados {len(files)} elementos recuperables.")

    def _selected_recoverable(self) -> RecoverableFile | None:
        row = self.recovery_table.currentRow()
        if row < 0:
            return None
        item = self.recovery_table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _recover_selected_original(self) -> None:
        file = self._selected_recoverable()
        if not file:
            QMessageBox.information(self, "Recuperar", "Selecciona un archivo de la lista.")
            return
        self._run_task(recover_file, self._recover_done, file, None)

    def _recover_selected_to(self) -> None:
        file = self._selected_recoverable()
        if not file:
            QMessageBox.information(self, "Recuperar", "Selecciona un archivo de la lista.")
            return
        directory = QFileDialog.getExistingDirectory(self, "Carpeta de recuperacion")
        if not directory:
            return
        self._run_task(recover_file, self._recover_done, file, Path(directory))

    def _recover_done(self, result: tuple[bool, str]) -> None:
        ok, message = result
        self.recovery_status.setText(message)
        QMessageBox.information(self, "Recuperar" if ok else "No se pudo recuperar", message)
        self._scan_recovery()

    def _load_installed_apps(self) -> None:
        self._run_task(list_installed_apps, self._installed_apps_done)

    def _installed_apps_done(self, apps: list[AppEntry]) -> None:
        self.installed_apps = apps
        self._filter_installed_apps()

    def _filter_installed_apps(self) -> None:
        query = self.installed_filter.text().strip().lower() if hasattr(self, "installed_filter") else ""
        rows = [app for app in self.installed_apps if query in app.name.lower()]
        self.installed_table.setRowCount(0)
        for app in rows:
            row = self.installed_table.rowCount()
            self.installed_table.insertRow(row)
            for col, value in enumerate((app.name, app.source, app.identifier, app.path)):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, app)
                self.installed_table.setItem(row, col, item)

    def _selected_app(self) -> AppEntry | None:
        row = self.installed_table.currentRow()
        if row < 0:
            return None
        item = self.installed_table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _uninstall_selected_app(self) -> None:
        app = self._selected_app()
        if not app:
            QMessageBox.information(self, "Aplicaciones", "Selecciona una app instalada.")
            return
        answer = QMessageBox.question(self, "Desinstalar", f"Quieres desinstalar {app.name}?")
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._run_task(uninstall_app, self._uninstall_app_done, app)

    def _uninstall_app_done(self, result: tuple[bool, str]) -> None:
        ok, message = result
        QMessageBox.information(self if ok else self, "Desinstalar", message)
        self._load_installed_apps()

    def _current_manager(self) -> PackageManager | None:
        key = self.manager_combo.currentData()
        for manager in self.managers:
            if manager.key == key:
                return manager
        return None

    def _require_manager_and_package(self, require_query: bool = False) -> tuple[PackageManager, str] | None:
        manager = self._current_manager()
        package_name = (self.package_name.text() or self.package_query.text()).strip()
        if require_query:
            package_name = self.package_query.text().strip()
        if not manager:
            QMessageBox.information(self, "Paquetes", "No hay gestor de paquetes disponible.")
            return None
        if not package_name:
            QMessageBox.information(self, "Paquetes", "Escribe un nombre o busqueda.")
            return None
        return manager, package_name

    def _search_packages(self) -> None:
        values = self._require_manager_and_package(require_query=True)
        if not values:
            return
        manager, query = values
        self.package_output.setPlainText("Buscando...")
        self._run_task(search, self._package_output_done, manager, query)

    def _list_packages(self) -> None:
        manager = self._current_manager()
        if not manager:
            QMessageBox.information(self, "Paquetes", "No hay gestor de paquetes disponible.")
            return
        self.package_output.setPlainText("Consultando instalados...")
        self._run_task(list_installed, self._package_output_done, manager)

    def _install_package(self) -> None:
        values = self._require_manager_and_package()
        if not values:
            return
        manager, package_name = values
        answer = QMessageBox.question(self, "Instalar", f"Instalar {package_name} con {manager.name}?")
        if answer == QMessageBox.StandardButton.Yes:
            self.package_output.setPlainText("Instalando...")
            self._run_task(install, self._package_output_done, manager, package_name)

    def _remove_package(self) -> None:
        values = self._require_manager_and_package()
        if not values:
            return
        manager, package_name = values
        answer = QMessageBox.question(self, "Desinstalar paquete", f"Desinstalar {package_name} con {manager.name}?")
        if answer == QMessageBox.StandardButton.Yes:
            self.package_output.setPlainText("Desinstalando...")
            self._run_task(uninstall, self._package_output_done, manager, package_name)

    def _package_output_done(self, result: tuple[int, str]) -> None:
        code, output = result
        self.package_output.setPlainText(f"Codigo: {code}\n\n{output or 'Sin salida.'}")

    def _pick_directory(self, field: QLineEdit) -> None:
        value = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
        if value:
            field.setText(value)

    def _pick_open_file(self, field: QLineEdit) -> None:
        value, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo")
        if value:
            field.setText(value)

    def _pick_save_file(self, field: QLineEdit) -> None:
        value, _ = QFileDialog.getSaveFileName(self, "Seleccionar destino")
        if value:
            field.setText(value)

    def _compress_folder(self) -> None:
        source = Path(self.compress_source.text().strip()).expanduser()
        dest_text = self.compress_dest.text().strip()
        destination = Path(dest_text).expanduser() if dest_text else source.with_name(source.name)
        archive_format = self.compress_format.currentText()
        self.archive_status.setText("Comprimiendo...")
        self._run_task(compress_folder, self._archive_done, source, destination, archive_format)

    def _extract_archive(self) -> None:
        source = Path(self.extract_source.text().strip()).expanduser()
        destination = Path(self.extract_dest.text().strip()).expanduser()
        self.archive_status.setText("Descomprimiendo...")
        self._run_task(extract_archive, self._archive_done, source, destination)

    def _archive_done(self, result: Path) -> None:
        self.archive_status.setText(f"Operacion completada: {result}")
        QMessageBox.information(self, "Archivos", f"Operacion completada:\n{result}")

    def _check_updates(self) -> None:
        self.update_status.setText("Consultando repositorio...")
        if hasattr(self, "help_update_status"):
            self.help_update_status.setText("Consultando repositorio...")
        self._run_task(check_updates, self._updates_done, __version__, ROOT)

    def _updates_done(self, info) -> None:
        self.update_status.setText(info.message)
        if hasattr(self, "help_update_status"):
            state = "Actualizacion disponible" if info.available else "Sin actualizaciones pendientes"
            self.help_update_status.setText(f"Version instalada: {__version__}. {state}. {info.message}")
        if not info.available:
            QMessageBox.information(self, "Actualizaciones", info.message)
            return
        answer = QMessageBox.question(self, "Actualizacion disponible", f"{info.message}\n\nQuieres instalar o abrir la actualizacion?")
        if answer != QMessageBox.StandardButton.Yes:
            return
        if info.can_git_pull:
            self._run_task(install_git_update, self._git_update_done, ROOT)
        elif info.url:
            webbrowser.open(info.url)

    def _git_update_done(self, result: tuple[bool, str]) -> None:
        ok, message = result
        suffix = "\n\nReinicia SysCare para ver los nuevos cambios." if ok else ""
        if hasattr(self, "help_update_status"):
            self.help_update_status.setText("Actualizacion instalada. Reinicia SysCare para cargar los cambios." if ok else "No se pudo instalar la actualizacion.")
        QMessageBox.information(self, "Actualizaciones", (message if message else ("Actualizado." if ok else "No se pudo actualizar.")) + suffix)


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(APP_QSS)
    window = MainWindow()
    window.show()
    window.start_open_animation()
    sys.exit(app.exec())
