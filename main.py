# -*- coding: utf-8 -*-
__version__ = "2.0.0"
"""Taxpanda 2.0 - registro sencillo de viajes y gastos.
Conserva el esquema SQLite movements de Taxpanda 1.x.
"""
import json
import sqlite3
import shutil
from datetime import datetime, date, timedelta
from pathlib import Path

from kivy.app import App
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.uix.image import Image as KivyImage

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase.pdfmetrics import stringWidth
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False

try:
    from jnius import autoclass, cast
    ANDROID_OK = True
except Exception:
    ANDROID_OK = False

# La base de datos conserva la ubicación y el formato de la versión anterior.
DB_PATH = Path(__file__).with_name("mi_trabajo.db")

TEXT = {
    "es": {
        "app_name": "Taxpanda", "home": "Inicio", "history": "Historial",
        "reports": "Reportes", "settings": "Configuración", "today": "RESUMEN DE HOY",
        "trips": "Viajes", "collected": "Ganancia total (bruta)", "fuel": "Gasolina",
        "other_expenses": "Otros gastos", "net": "Ganancia neta", "add_trip": "+ REGISTRAR VIAJE",
        "add_fuel": "REGISTRAR GASOLINA", "add_expense": "OTRO GASTO",
        "backup": "Copia de seguridad", "create_backup": "Crear copia de seguridad", "restore_backup": "Restaurar copia", "restore_confirm": "Restaurar esta copia reemplazará los registros actuales. Antes se guardará una copia de seguridad automática. ¿Continuar?", "restore_done": "Copia restaurada correctamente.", "restore_none": "No hay copias de seguridad disponibles.", "restore_error": "No se pudo restaurar la copia. Tus registros actuales no se han reemplazado.", "date": "Fecha", "choose_date": "Elegir fecha",
        "show": "Mostrar", "close": "Cerrar", "edit": "Editar", "delete": "Borrar",
        "save": "Guardar", "cancel": "Cancelar", "amount": "Importe (ej. 2.00)",
        "detail": "Descripción", "no_movements": "No hay movimientos para esta fecha.",
        "invalid_date": "La fecha no es válida.", "invalid_amount": "Escribe un importe válido mayor que cero.",
        "new_trip": "Nuevo viaje", "fuel_title": "Gasolina", "other_title": "Otro gasto",
        "movement_saved": "Movimiento guardado.", "edit_movement": "Editar movimiento",
        "confirm_delete": "¿Quieres borrar este movimiento?", "backup_done": "Copia de seguridad creada.",
        "backup_error": "No se pudo crear la copia de seguridad.", "period": "Período",
        "today_preset": "Hoy", "yesterday": "Ayer", "this_week": "Esta semana",
        "last_week": "Semana pasada", "this_month": "Este mes", "custom": "Personalizado",
        "start_date": "Fecha inicial", "end_date": "Fecha final", "generate_pdf": "GENERAR PDF",
        "share_pdf": "COMPARTIR PDF", "pdf_created": "PDF creado correctamente.",
        "check_dates": "Revisa las fechas seleccionadas.", "need_reportlab": "No está disponible el módulo para generar PDF.",
        "pdf_title": "TAXPANDA - REPORTE", "period_label": "Período", "daily_total": "Resumen del día",
        "total_period": "TOTAL DEL PERÍODO", "other": "Otro", "trip": "Viaje",
        "language": "Idioma", "spanish": "Español", "english": "Inglés", "appearance": "Apariencia",
        "day_mode": "Modo día", "night_mode": "Modo noche", "save_settings": "Guardar preferencias",
        "settings_saved": "Preferencias guardadas.", "theme": "Tema", "no_data": "Todavía no hay movimientos.",
        "choose_action": "Acciones", "deleted": "Movimiento borrado.", "pdf_saved": "PDF guardado en Descargas/Mi Trabajo.",
        "share_error": "No se pudo abrir el menú para compartir. El PDF fue generado.",
        "other_type": "Tipo de gasto", "wash": "Lavado", "repair": "Reparación", "oil": "Aceite",
        "food": "Comida", "toll": "Peaje", "other_option": "Otro", "select_language": "Selecciona el idioma",
        "select_theme": "Selecciona la apariencia", "edit_backup_note": "La copia incluye tus registros.",
        "cash": "Caja", "reset_test_data": "Reiniciar registros de prueba", "reset_confirm": "Esto borrará los viajes, gastos, aportes, recuperaciones, fondos de apertura y estados diarios. No se puede deshacer. ¿Quieres continuar?", "reset_done": "Los registros de prueba se borraron. La configuración se conservó.", "reset_error": "No se pudieron borrar los registros.", "initial_change": "Fondo de apertura", "pocket_contributions": "Aportes personales", "recovered": "Reembolsos realizados", "pending_recovery": "Saldo por reembolsar", "set_change": "Configurar cambio inicial", "register_recovery": "Registrar recuperación", "recovery_amount": "Importe a recuperar", "payment_source": "Fuente de los fondos", "my_pocket": "Fondos personales", "cash_money": "Ingresos por viajes", "change_note": "Dinero para dar vuelto. No cuenta como ganancia.", "operating_fund": "Fondo del propietario", "own_money": "Fondos personales", "initial_source": "Fuente del fondo de apertura", "recovery_note": "La recuperación devuelve tu aporte; no es una ganancia nueva.", "cash_saved": "Cambio inicial guardado.", "recovery_saved": "Recuperación registrada.", "no_pending": "No tienes aportes pendientes de recuperar.",
        "day_status": "Estado del día", "save_day_status": "Guardar estado", "worked": "Trabajé", "not_worked": "No trabajé", "rest_day": "Descanso", "unregistered": "Sin registrar", "pending_day": "Pendiente", "status_saved": "Estado del día guardado.",
    },
    "en": {
        "app_name": "Taxpanda", "home": "Home", "history": "History", "reports": "Reports",
        "settings": "Settings", "today": "TODAY'S SUMMARY", "trips": "Trips", "collected": "Gross trip income",
        "fuel": "Fuel", "other_expenses": "Other expenses", "net": "Net earnings", "add_trip": "+ ADD TRIP",
        "add_fuel": "ADD FUEL", "add_expense": "OTHER EXPENSE", "backup": "Backup", "restore_backup": "Restore backup", "restore_confirm": "Restoring this backup will replace current records. A safety backup will be created first. Continue?", "restore_done": "Backup restored successfully.", "restore_none": "No backups are available.", "restore_error": "Could not restore the backup. Your current records have not been replaced.", "date": "Date",
        "choose_date": "Choose date", "show": "Show", "close": "Close", "edit": "Edit", "delete": "Delete", "create_backup": "Create backup",
        "save": "Save", "cancel": "Cancel", "amount": "Amount (e.g. 2.00)", "detail": "Description",
        "no_movements": "There are no movements for this date.", "invalid_date": "The date is not valid.",
        "invalid_amount": "Enter a valid amount greater than zero.", "new_trip": "New trip", "fuel_title": "Fuel",
        "other_title": "Other expense", "movement_saved": "Movement saved.", "edit_movement": "Edit movement",
        "confirm_delete": "Do you want to delete this movement?", "backup_done": "Backup created.",
        "backup_error": "Could not create the backup.", "period": "Period", "today_preset": "Today", "yesterday": "Yesterday",
        "this_week": "This week", "last_week": "Last week", "this_month": "This month", "custom": "Custom",
        "start_date": "Start date", "end_date": "End date", "generate_pdf": "GENERATE PDF", "share_pdf": "SHARE PDF",
        "pdf_created": "PDF created successfully.", "check_dates": "Check the selected dates.",
        "need_reportlab": "The PDF generation module is unavailable.", "pdf_title": "TAXPANDA - REPORT",
        "period_label": "Period", "daily_total": "Daily summary", "total_period": "PERIOD TOTAL", "other": "Other",
        "trip": "Trip", "language": "Language", "spanish": "Spanish", "english": "English",
        "appearance": "Appearance", "day_mode": "Day mode", "night_mode": "Night mode", "save_settings": "Save preferences",
        "settings_saved": "Preferences saved.", "theme": "Theme", "no_data": "There are no movements yet.",
        "choose_action": "Actions", "deleted": "Movement deleted.", "pdf_saved": "PDF saved to Downloads/Mi Trabajo.",
        "share_error": "Could not open the share menu. The PDF was generated.", "other_type": "Expense type", "wash": "Car wash",
        "repair": "Repair", "oil": "Oil", "food": "Food", "toll": "Toll", "other_option": "Other",
        "select_language": "Choose language", "select_theme": "Choose appearance", "edit_backup_note": "The backup includes your records.",
        "cash": "Cash box", "reset_test_data": "Reset test records", "reset_confirm": "This will delete trips, expenses, contributions, reimbursements, opening funds, and daily statuses. This cannot be undone. Continue?", "reset_done": "Test records deleted. Settings were preserved.", "reset_error": "Could not delete the records.", "initial_change": "Opening fund", "pocket_contributions": "Personal contributions", "recovered": "Reimbursements made", "pending_recovery": "Balance to reimburse", "set_change": "Set starting change", "register_recovery": "Register reimbursement", "recovery_amount": "Amount to reimburse", "payment_source": "Funding source", "my_pocket": "Personal funds", "cash_money": "Trip income", "change_note": "Money for giving change. It is not earnings.", "operating_fund": "Owner fund", "own_money": "Personal funds", "initial_source": "Opening-fund source", "recovery_note": "Reimbursement returns your contribution; it is not new profit.", "cash_saved": "Starting change saved.", "recovery_saved": "Reimbursement recorded.", "no_pending": "You have no contributions awaiting reimbursement.",
        "day_status": "Day status", "save_day_status": "Save status", "worked": "Worked", "not_worked": "Did not work", "rest_day": "Day off", "unregistered": "Not marked", "pending_day": "Pending", "status_saved": "Day status saved.",
    }
}

POPUP_BG = "#FFFFFF"
POPUP_TEXT = "#17452F"
POPUP_FIELD = "#EFF7F1"
POPUP_ACCENT = "#DDEFE2"
POPUP_GREEN = "#16834A"

class GreenSpinnerOption(SpinnerOption):
    """Opción de lista con contraste consistente en Android."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = get_color_from_hex("#DDEFE2")
        self.color = get_color_from_hex("#17452F")
        self.font_size = dp(15)


THEMES = {
    "day": {"bg": "#F4F7F5", "surface": "#FFFFFF", "text": "#17251D", "muted": "#69766E", "primary": "#16834A", "primary_text": "#FFFFFF", "danger": "#C83C3C", "line": "#DCE5DF", "field": "#FFFFFF"},
    "night": {"bg": "#111714", "surface": "#1D2621", "text": "#F1F5F2", "muted": "#B1BDB5", "primary": "#38B873", "primary_text": "#102016", "danger": "#FF7777", "line": "#35423A", "field": "#27332C"},
}

class TaxpandaApp(App):
    def build(self):
        self.title = "Taxpanda"
        self.settings_path = Path(self.user_data_dir) / "preferencias.json"
        self.preferences = self.load_preferences()
        self.lang = self.preferences.get("language", "es")
        self.theme_name = self.preferences.get("theme", "day")
        self.colors = THEMES[self.theme_name]
        self.create_db()
        self.show_home()
        return self.root_layout

    def t(self, key):
        return TEXT.get(self.lang, TEXT["es"]).get(key, TEXT["es"].get(key, key))

    def load_preferences(self):
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8"))
            if data.get("language") not in ("es", "en"):
                data["language"] = "es"
            if data.get("theme") not in ("day", "night"):
                data["theme"] = "day"
            return data
        except Exception:
            return {"language": "es", "theme": "day"}

    def save_preferences(self):
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings_path.write_text(json.dumps({"language": self.lang, "theme": self.theme_name}, ensure_ascii=False), encoding="utf-8")

    def create_db(self):
        con = sqlite3.connect(DB_PATH)
        con.execute("""CREATE TABLE IF NOT EXISTS movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, amount REAL NOT NULL,
            detail TEXT, created_at TEXT NOT NULL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS daily_cash (
            day TEXT PRIMARY KEY, initial_change REAL NOT NULL DEFAULT 0,
            initial_source TEXT NOT NULL DEFAULT 'Fondo operativo')""")
        # Migrate older databases without deleting or replacing existing records.
        columns = [row[1] for row in con.execute("PRAGMA table_info(daily_cash)").fetchall()]
        if "initial_source" not in columns:
            con.execute("ALTER TABLE daily_cash ADD COLUMN initial_source TEXT NOT NULL DEFAULT 'Fondo operativo'")
        con.execute("""CREATE TABLE IF NOT EXISTS daily_cash_funds (
            day TEXT NOT NULL, source TEXT NOT NULL, amount REAL NOT NULL DEFAULT 0,
            PRIMARY KEY(day, source))""")
        legacy_rows = con.execute(
            """SELECT day, initial_change, initial_source FROM daily_cash
               WHERE day NOT IN (SELECT DISTINCT day FROM daily_cash_funds)"""
        ).fetchall()
        for legacy_day, legacy_amount, legacy_source in legacy_rows:
            con.execute(
                "INSERT OR IGNORE INTO daily_cash_funds(day, source, amount) VALUES(?,?,?)",
                (legacy_day, (self.t("own_money") if legacy_source in ("Dinero propio", "Own money") else self.t("operating_fund")), float(legacy_amount or 0))
            )
        con.execute("""CREATE TABLE IF NOT EXISTS personal_contributions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, day TEXT NOT NULL, amount REAL NOT NULL,
            category TEXT NOT NULL, detail TEXT DEFAULT '', recovered REAL NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL, movement_id INTEGER)""")
        contribution_columns = [row[1] for row in con.execute("PRAGMA table_info(personal_contributions)").fetchall()]
        if "movement_id" not in contribution_columns:
            con.execute("ALTER TABLE personal_contributions ADD COLUMN movement_id INTEGER")
        con.execute("""CREATE TABLE IF NOT EXISTS movement_funding (
            movement_id INTEGER PRIMARY KEY, source TEXT NOT NULL DEFAULT 'Ingresos por viajes')""")
        con.execute("""CREATE TABLE IF NOT EXISTS day_status (
            day TEXT PRIMARY KEY, status TEXT NOT NULL, updated_at TEXT NOT NULL)""")
        con.commit(); con.close()

    def label(self, text="", size=15, bold=False, color=None, **kwargs):
        lbl = Label(text=text, font_size=dp(size), bold=bold, color=get_color_from_hex(color or self.colors["text"]), **kwargs)
        lbl.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        return lbl

    def button(self, text, callback, color=None, text_color=None, height=48, font_size=15):
        b = Button(text=text, size_hint_y=None, height=dp(height), font_size=dp(font_size), bold=True,
                   background_normal="", background_down="", background_color=get_color_from_hex(color or self.colors["surface"]),
                   color=get_color_from_hex(text_color or self.colors["text"]))
        b.bind(on_release=callback)
        return b

    def base(self):
        root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        root.canvas.before.clear()
        from kivy.graphics import Color, Rectangle
        with root.canvas.before:
            Color(*get_color_from_hex(self.colors["bg"]))
            root._bg_rect = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda w, p: setattr(root._bg_rect, "pos", p), size=lambda w, s: setattr(root._bg_rect, "size", s))
        return root

    def card(self, children=None, padding=12, spacing=8, orientation="vertical"):
        box = BoxLayout(orientation=orientation, padding=dp(padding), spacing=dp(spacing), size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))
        if children:
            for child in children: box.add_widget(child)
        return box

    def popup(self, title, content, size_hint=(0.9, 0.5)):
        # Fondo blanco real y título verde oscuro para que el contraste no dependa del tema global.
        return Popup(title=title, content=content, size_hint=size_hint,
                     background="", background_color=get_color_from_hex(POPUP_BG),
                     title_color=get_color_from_hex(POPUP_TEXT),
                     separator_color=get_color_from_hex(POPUP_GREEN))

    def popup_label(self, text="", size=15, bold=False, **kwargs):
        return self.label(text, size, bold, color=POPUP_TEXT, **kwargs)

    def popup_button(self, text, callback, primary=False, height=48, font_size=15):
        return self.button(text, callback,
                           POPUP_GREEN if primary else POPUP_ACCENT,
                           "#FFFFFF" if primary else POPUP_TEXT,
                           height, font_size)

    def show_home(self, *_):
        """Inicio compacto: indicadores separados y desplazables en pantallas pequeñas."""
        self.colors = THEMES[self.theme_name]
        root = self.base()
        root.padding = dp(12)
        root.spacing = dp(5)

        header = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        logo_path = Path(__file__).with_name("taxpanda_logo.png")
        if logo_path.exists():
            logo = KivyImage(source=str(logo_path), size_hint=(None, 1), width=dp(42), allow_stretch=True, keep_ratio=True)
            header.add_widget(logo)
        title = self.label("Taxpanda", 22, True, self.colors["primary"], halign="left", valign="middle")
        title.size_hint_x = 1
        header.add_widget(title)
        header.add_widget(self.button("Ajustes", self.show_settings, height=42, font_size=12))
        root.add_widget(header)
        self.clock = self.label(datetime.now().strftime("%d/%m/%Y  %I:%M %p"), 12, color=self.colors["text"], halign="left")
        # Keep the clock row compact. Without a fixed height, Kivy's default
        # size_hint_y lets it expand and pushes the dashboard far down the screen.
        self.clock.size_hint_y = None
        self.clock.height = dp(20)
        root.add_widget(self.clock)

        scroll = ScrollView(do_scroll_x=False, bar_width=dp(3), scroll_y=1)
        content = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None, padding=(0, dp(1), 0, dp(12)))
        content.bind(minimum_height=content.setter("height"))

        from kivy.graphics import Color, RoundedRectangle
        dashboard = BoxLayout(orientation="vertical", padding=dp(9), spacing=dp(6), size_hint_y=None)
        dashboard.bind(minimum_height=dashboard.setter("height"))
        with dashboard.canvas.before:
            Color(*get_color_from_hex(self.colors["surface"]))
            dashboard._rr = RoundedRectangle(pos=dashboard.pos, size=dashboard.size, radius=[dp(18)])
        dashboard.bind(pos=lambda w,p: setattr(dashboard._rr,"pos",p), size=lambda w,s: setattr(dashboard._rr,"size",s))

        top = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(6))
        top.add_widget(self.label(self.t("today"), 14, True, self.colors["text"], halign="left"))
        top.add_widget(self.label(date.today().strftime("%d/%m/%Y"), 12, False, self.colors["muted"], halign="right"))
        dashboard.add_widget(top)

        tiles = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, row_default_height=dp(78), row_force_default=True)
        tiles.bind(minimum_height=tiles.setter("height"))
        tile_specs = [
            ("trips_tile", self.t("trips"), "#E7F2FF", "#1769AA"),
            ("collected_tile", self.t("collected"), "#E8F5EB", "#16834A"),
            ("fuel_tile", self.t("fuel"), "#FCEBEC", "#C83C3C"),
            ("other_tile", self.t("other_expenses"), "#FFF0E2", "#B96313"),
        ]
        self.metric_labels = {}
        for key, caption, bg, fg in tile_specs:
            tile = BoxLayout(orientation="vertical", padding=dp(5), spacing=dp(1))
            with tile.canvas.before:
                Color(*get_color_from_hex(bg))
                tile._rr = RoundedRectangle(pos=tile.pos, size=tile.size, radius=[dp(13)])
            tile.bind(pos=lambda w,p: setattr(w._rr,"pos",p), size=lambda w,s: setattr(w._rr,"size",s))
            tile.add_widget(self.label(caption, 11, True, fg, halign="center"))
            value_lbl = self.label("0", 18, True, fg, halign="center")
            tile.add_widget(value_lbl)
            self.metric_labels[key] = value_lbl
            tiles.add_widget(tile)
        dashboard.add_widget(tiles)

        net_box = BoxLayout(orientation="vertical", padding=dp(6), spacing=dp(0), size_hint_y=None, height=dp(64))
        with net_box.canvas.before:
            Color(*get_color_from_hex("#E7F5EB" if self.theme_name == "day" else "#243D2E"))
            net_box._rr = RoundedRectangle(pos=net_box.pos, size=net_box.size, radius=[dp(13)])
        net_box.bind(pos=lambda w,p: setattr(net_box._rr,"pos",p), size=lambda w,s: setattr(net_box._rr,"size",s))
        net_box.add_widget(self.label(self.t("net"), 12, True, self.colors["primary"], halign="center"))
        self.net_label = self.label("$0.00", 24, True, self.colors["primary"], halign="center")
        net_box.add_widget(self.net_label)
        dashboard.add_widget(net_box)

        cash_tiles = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, row_default_height=dp(68), row_force_default=True)
        cash_tiles.bind(minimum_height=cash_tiles.setter("height"))
        for key, caption, bg, fg in [
            ("contributed_tile", self.t("pocket_contributions"), "#F1E6FF", "#7136A8"),
            ("initial_tile", self.t("initial_change"), "#E5F2FF", "#1769AA"),
        ]:
            tile=BoxLayout(orientation="vertical",padding=dp(4),spacing=dp(1))
            with tile.canvas.before:
                Color(*get_color_from_hex(bg)); tile._rr=RoundedRectangle(pos=tile.pos,size=tile.size,radius=[dp(12)])
            tile.bind(pos=lambda w,p:setattr(w._rr,"pos",p),size=lambda w,s:setattr(w._rr,"size",s))
            tile.add_widget(self.label(caption,10,True,fg,halign="center"))
            val=self.label("$0.00",16,True,fg,halign="center"); tile.add_widget(val); self.metric_labels[key]=val
            cash_tiles.add_widget(tile)
        dashboard.add_widget(cash_tiles)

        pending_box=BoxLayout(orientation="vertical",padding=dp(6),spacing=dp(0),size_hint_y=None,height=dp(52))
        with pending_box.canvas.before:
            Color(*get_color_from_hex("#FFF0D4" if self.theme_name == "day" else "#44351F")); pending_box._rr=RoundedRectangle(pos=pending_box.pos,size=pending_box.size,radius=[dp(12)])
        pending_box.bind(pos=lambda w,p:setattr(w._rr,"pos",p),size=lambda w,s:setattr(w._rr,"size",s))
        pending_box.add_widget(self.label(self.t("pending_recovery"),11,True,"#A64B12",halign="center"))
        self.pending_label=self.label("$0.00",18,True,"#A64B12",halign="center")
        pending_box.add_widget(self.pending_label); dashboard.add_widget(pending_box)

        # Indicador visible en Inicio: dinero disponible de los viajes después de gastos
        # pagados con la caja y reembolsos, más el fondo del dueño que siga en caja.
        physical_box = BoxLayout(orientation="vertical", padding=dp(6), spacing=dp(0), size_hint_y=None, height=dp(58))
        with physical_box.canvas.before:
            Color(*get_color_from_hex("#DDF3F0" if self.theme_name == "day" else "#203F3B"))
            physical_box._rr = RoundedRectangle(pos=physical_box.pos, size=physical_box.size, radius=[dp(12)])
        physical_box.bind(pos=lambda w,p:setattr(w._rr,"pos",p), size=lambda w,s:setattr(w._rr,"size",s))
        physical_box.add_widget(self.label("Dinero físico disponible" if self.lang == "es" else "Physical cash available", 11, True, "#176B62", halign="center"))
        self.physical_cash_label = self.label("$0.00", 20, True, "#176B62", halign="center")
        physical_box.add_widget(self.physical_cash_label)
        dashboard.add_widget(physical_box)
        content.add_widget(dashboard)

        content.add_widget(self.button(self.t("add_trip"), self.add_trip, self.colors["primary"], self.colors["primary_text"], 48, 15))
        row=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(8))
        row.add_widget(self.button(self.t("add_fuel"),self.add_gas,self.colors["danger"],"#FFFFFF",44,10))
        row.add_widget(self.button(self.t("add_expense"),self.add_other,"#E8A23A","#241A08",44,10))
        content.add_widget(row)
        scroll.add_widget(content)
        # In Kivy, set the initial scroll position after the first layout so the dashboard
        # does not appear far below the header on some Android screen sizes.
        from kivy.clock import Clock
        Clock.schedule_once(lambda *_: setattr(scroll, "scroll_y", 1), 0.15)
        root.add_widget(scroll)

        nav=GridLayout(cols=5,size_hint_y=None,height=dp(56),spacing=dp(3))
        for txt,fn in [(self.t("home"),self.show_home),(self.t("history"),self.show_history),(self.t("reports"),self.show_reports),(self.t("cash"),self.show_cash),(self.t("settings"),self.show_settings)]:
            nav.add_widget(self.button(txt,fn,self.colors["surface"],self.colors["text"],56,10))
        root.add_widget(nav)
        self.root_layout=root
        self.update_screen()

    def next_trip_number(self, day=None):
        day = day or date.today().isoformat()
        con = sqlite3.connect(DB_PATH)
        n = con.execute("SELECT COUNT(*) FROM movements WHERE kind='viaje' AND date(created_at)=?", (day,)).fetchone()[0]
        con.close(); return n + 1

    def save_movement(self, kind, amount, detail=""):
        con = sqlite3.connect(DB_PATH)
        cur = con.execute("INSERT INTO movements(kind,amount,detail,created_at) VALUES(?,?,?,?)", (kind, amount, detail, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        movement_id = cur.lastrowid
        con.commit(); con.close(); self.update_screen()
        return movement_id

    def day_rows(self, d):
        con = sqlite3.connect(DB_PATH)
        rows = con.execute("SELECT id,kind,amount,detail,created_at FROM movements WHERE date(created_at)=? ORDER BY created_at,id", (d,)).fetchall()
        con.close(); return rows

    def totals(self, rows):
        trips = sum(a for _,k,a,_,_ in rows if k == "viaje")
        gas = sum(a for _,k,a,_,_ in rows if k == "gasolina")
        other = sum(a for _,k,a,_,_ in rows if k == "otro")
        count = sum(1 for _,k,_,_,_ in rows if k == "viaje")
        return count, trips, gas, other, trips-gas-other

    def update_screen(self):
        if not hasattr(self, "net_label"): return
        rows = self.day_rows(date.today().isoformat())
        count, trips, gas, other, net = self.totals(rows)
        self.clock.text = datetime.now().strftime("%d/%m/%Y  %I:%M %p")
        self.net_label.text = f"${net:.2f}"
        initial, contributed, recovered, pending = self.cash_totals(date.today().isoformat())
        labels = getattr(self, "metric_labels", {})
        values = {"trips_tile": str(count), "collected_tile": f"${trips:.2f}",
                  "fuel_tile": f"${gas:.2f}", "other_tile": f"${other:.2f}",
                  "contributed_tile": f"${contributed:.2f}", "initial_tile": f"${initial:.2f}"}
        for key, value in values.items():
            if key in labels: labels[key].text = value
        if hasattr(self, "pending_label"):
            self.pending_label.text = f"${pending:.2f}"
        if hasattr(self, "physical_cash_label"):
            con = sqlite3.connect(DB_PATH)
            funds = con.execute(
                "SELECT source, COALESCE(SUM(amount),0) FROM daily_cash_funds WHERE day=? GROUP BY source",
                (date.today().isoformat(),)
            ).fetchall()
            funded_rows = con.execute(
                "SELECT m.amount, COALESCE(f.source, ?) FROM movements m "
                "LEFT JOIN movement_funding f ON f.movement_id=m.id "
                "WHERE date(m.created_at)=? AND m.kind IN ('gasolina','otro')",
                (self.t("cash_money"), date.today().isoformat())
            ).fetchall()
            con.close()
            owner_sources = (self.t("operating_fund"), "Dinero del jefe", "Boss money", "Fondo de operación", "Operating fund")
            pocket_sources = (self.t("own_money"), "Dinero propio", "Own money", "Fondos personales")
            owner_fund = sum(float(a) for src, a in funds if src in owner_sources)
            owner_expenses = sum(float(a) for a, src in funded_rows if src in owner_sources)
            trip_expenses = sum(float(a) for a, src in funded_rows if src not in owner_sources and src not in pocket_sources)
            available = max(0.0, trips - trip_expenses - recovered + max(0.0, owner_fund-owner_expenses))
            self.physical_cash_label.text = f"${available:.2f}"

    def form_popup(self, title, kind, trip_number=None, choices=None, existing=None, on_saved=None):
        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        if trip_number:
            box.add_widget(self.popup_label(f"{self.t('trip')} {trip_number}", 20, True))
        amount = TextInput(text=(f"{existing[0]:.2f}" if existing else ""),
            hint_text="Cantidad que vas a agregar", input_filter="float", multiline=False,
            font_size=dp(21), size_hint_y=None, height=dp(54),
            foreground_color=get_color_from_hex(POPUP_TEXT),
            background_color=get_color_from_hex(POPUP_FIELD), cursor_color=get_color_from_hex(POPUP_GREEN))
        box.add_widget(amount)
        detail = None
        payment_source = None
        existing_source = self.t("cash_money")
        if existing and kind in ("gasolina", "otro"):
            con = sqlite3.connect(DB_PATH)
            linked = con.execute(
                "SELECT id FROM personal_contributions WHERE movement_id=? ORDER BY id LIMIT 1",
                (existing[2],)
            ).fetchone()
            fund = con.execute("SELECT source FROM movement_funding WHERE movement_id=?", (existing[2],)).fetchone()
            con.close()
            if linked:
                existing_source = self.t("my_pocket")
            elif fund and fund[0] in ("Dinero del jefe", "Boss money", self.t("operating_fund")):
                existing_source = self.t("operating_fund")
        if kind in ("gasolina", "otro"):
            box.add_widget(self.popup_label(self.t("payment_source"), 13, True))
            payment_source = Spinner(option_cls=GreenSpinnerOption, text=existing_source,
                values=(self.t("my_pocket"), self.t("cash_money"), self.t("operating_fund")), size_hint_y=None, height=dp(46),
                color=get_color_from_hex(POPUP_TEXT), background_normal="",
                background_color=get_color_from_hex(POPUP_ACCENT))
            box.add_widget(payment_source)
        if choices:
            detail = Spinner(option_cls=GreenSpinnerOption,
                text=(existing[1] if existing and existing[1] else choices[0]),
                values=choices, size_hint_y=None, height=dp(48),
                color=get_color_from_hex(POPUP_TEXT), background_normal="",
                background_color=get_color_from_hex(POPUP_ACCENT))
            box.add_widget(detail)
        elif existing:
            detail = TextInput(text=existing[1] or "", hint_text=self.t("detail"),
                multiline=False, size_hint_y=None, height=dp(48))
            box.add_widget(detail)
        buttons = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        pop = self.popup(title, box, (0.9, 0.58 if kind in ("gasolina", "otro") else 0.48))
        buttons.add_widget(self.popup_button(self.t("cancel"), pop.dismiss, height=48))

        def save(*_):
            try:
                value = float(amount.text.replace(",", "."))
                if value <= 0:
                    raise ValueError
            except Exception:
                self.message(title, self.t("invalid_amount"))
                return
            desc = detail.text if detail else ""
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if existing:
                try:
                    self.backup_database()
                except Exception:
                    self.message(self.t("backup"), self.t("backup_error"))
                    return
                con = sqlite3.connect(DB_PATH)
                try:
                    linked = con.execute(
                        "SELECT id, recovered FROM personal_contributions WHERE movement_id=? ORDER BY id LIMIT 1",
                        (existing[2],)
                    ).fetchone()
                    selected_source = payment_source.text if payment_source is not None else self.t("cash_money")
                    wants_pocket = selected_source == self.t("my_pocket")
                    if linked and float(linked[1]) > value + 0.0001:
                        con.rollback()
                        self.message(title, "No puedes reducir el gasto por debajo del importe ya recuperado.")
                        con.close()
                        return
                    con.execute("UPDATE movements SET amount=?,detail=? WHERE id=?", (value, desc, existing[2]))
                    if kind in ("gasolina", "otro"):
                        if wants_pocket:
                            if linked:
                                con.execute("UPDATE personal_contributions SET amount=?,detail=? WHERE id=?",
                                    (value, desc or title, linked[0]))
                            else:
                                movement_day = con.execute(
                                    "SELECT date(created_at) FROM movements WHERE id=?", (existing[2],)
                                ).fetchone()[0]
                                con.execute(
                                    """INSERT INTO personal_contributions
                                       (day,amount,category,detail,recovered,created_at,movement_id)
                                       VALUES(?,?,?,?,0,?,?)""",
                                    (movement_day, value, kind, desc or title, now, existing[2]))
                        elif linked:
                            if float(linked[1]) > 0.0001:
                                con.rollback()
                                self.message(title, "No puedes cambiar el origen porque este gasto ya tiene una recuperación registrada.")
                                con.close()
                                return
                            con.execute("DELETE FROM personal_contributions WHERE id=?", (linked[0],))
                        con.execute("INSERT INTO movement_funding(movement_id,source) VALUES(?,?) ON CONFLICT(movement_id) DO UPDATE SET source=excluded.source", (existing[2], selected_source))
                    con.commit()
                except Exception:
                    con.rollback()
                    con.close()
                    self.message(title, "No se pudo actualizar el movimiento.")
                    return
                con.close()
            else:
                movement_id = self.save_movement(kind, value, desc)
                if payment_source is not None:
                    con = sqlite3.connect(DB_PATH)
                    con.execute("INSERT INTO movement_funding(movement_id,source) VALUES(?,?) ON CONFLICT(movement_id) DO UPDATE SET source=excluded.source", (movement_id, payment_source.text))
                    if payment_source.text == self.t("my_pocket"):
                        con.execute(
                            """INSERT INTO personal_contributions
                               (day,amount,category,detail,recovered,created_at,movement_id)
                               VALUES(?,?,?,?,0,?,?)""",
                            (date.today().isoformat(), value, kind, desc or title, now, movement_id))
                    con.commit()
                    con.close()
            pop.dismiss()
            self.update_screen()
            if on_saved:
                on_saved()

        buttons.add_widget(self.popup_button(self.t("save"), save, primary=True, height=48))
        box.add_widget(buttons)
        pop.open()

    def add_trip(self, *_): self.form_popup(self.t("new_trip"), "viaje", self.next_trip_number())
    def add_gas(self, *_): self.form_popup(self.t("fuel_title"), "gasolina")
    def add_other(self, *_):
        choices = (self.t("wash"), self.t("repair"), self.t("oil"), self.t("food"), self.t("toll"), self.t("other_option"))
        self.form_popup(self.t("other_title"), "otro", choices=choices)

    def cash_totals(self, day):
        con = sqlite3.connect(DB_PATH)
        row = con.execute("SELECT initial_change FROM daily_cash WHERE day=?", (day,)).fetchone()
        initial = float(row[0]) if row else 0.0
        row = con.execute("SELECT COALESCE(SUM(amount),0), COALESCE(SUM(recovered),0) FROM personal_contributions WHERE day=?", (day,)).fetchone()
        con.close()
        contributed, recovered = float(row[0]), float(row[1])
        return initial, contributed, recovered, max(0.0, contributed - recovered)

    def show_cash(self, *_):
        day = date.today().isoformat()

        # Ventana desplazable para que el resumen y los botones no se monten.
        outer = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(4), scroll_y=1)
        content = BoxLayout(
            orientation="vertical", padding=dp(8), spacing=dp(12),
            size_hint_y=None
        )
        content.bind(minimum_height=content.setter("height"))

        def add_text(text="", size=14, bold=False):
            label = self.popup_label(text, size, bold, halign="left", valign="middle")
            label.size_hint_y = None
            label.text_size = (dp(280), None)
            label.bind(texture_size=lambda inst, value: setattr(inst, "height", value[1] + dp(12)))
            content.add_widget(label)
            return label

        add_text(f"{self.t('cash')} • {date.today().strftime('%d/%m/%Y')}", 18, True)
        cash_info = add_text("", 14)
        contribution_info = add_text("", 14)
        pending_info = add_text("", 14, True)

        buttons = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(7))
        buttons.add_widget(self.popup_button(
            self.t("set_change"),
            lambda *_: (pop.dismiss(), self.set_initial_change()),
            height=48, font_size=11
        ))
        buttons.add_widget(self.popup_button(
            self.t("register_recovery"),
            lambda *_: (pop.dismiss(), self.register_recovery()),
            primary=True, height=48, font_size=11
        ))
        content.add_widget(buttons)

        add_text("RESUMEN DEL DÍA" if self.lang == "es" else "DAILY SUMMARY", 16, True)
        summary = add_text("", 14, False)

        def refresh_summary(*_):
            initial, contributed, recovered, pending = self.cash_totals(day)
            con_funds = sqlite3.connect(DB_PATH)
            fund_rows = con_funds.execute(
                "SELECT source, amount FROM daily_cash_funds WHERE day=? ORDER BY source",
                (day,)
            ).fetchall()
            con_funds.close()
            fund_lines = []
            for source_name, fund_amount in fund_rows:
                fund_label = source_name
                if source_name in ("Dinero propio", "Own money"):
                    fund_label = self.t("own_money")
                elif source_name in ("Fondo operativo", "Operating fund"):
                    fund_label = self.t("operating_fund")
                fund_lines.append(f"  • {fund_label}: ${float(fund_amount):.2f}")
            fund_detail = "\\n".join(fund_lines)
            cash_info.text = (
                f"{self.t('initial_change')}: ${initial:.2f}"
                + (f"\\n{fund_detail}" if fund_detail else "")
                + f"\\n{self.t('change_note')}"
            )
            contribution_info.text = (
                f"{self.t('pocket_contributions')}: ${contributed:.2f}\n"
                f"{self.t('recovered')}: ${recovered:.2f}"
            )
            pending_info.text = (
                f"{self.t('pending_recovery')}: ${pending:.2f}\n{self.t('recovery_note')}"
            )

            rows = self.day_rows(day)
            count, collected, fuel, other, net = self.totals(rows)
            con = sqlite3.connect(DB_PATH)
            pocket_by_kind = con.execute(
                "SELECT category, COALESCE(SUM(amount),0) "
                "FROM personal_contributions WHERE day=? GROUP BY category",
                (day,)
            ).fetchall()
            owner_fund_row = con.execute(
                "SELECT COALESCE(SUM(amount),0) FROM daily_cash_funds WHERE day=? AND source IN ('Dinero del jefe','Boss money','Fondo de operación','Operating fund')",
                (day,)
            ).fetchone()
            funded_rows = con.execute(
                "SELECT m.kind, m.amount, COALESCE(f.source, 'Ingresos por viajes') FROM movements m LEFT JOIN movement_funding f ON f.movement_id=m.id WHERE date(m.created_at)=? AND m.kind IN ('gasolina','otro')",
                (day,)
            ).fetchall()
            con.close()
            pocket = {kind: float(amount) for kind, amount in pocket_by_kind}
            all_expenses = fuel + other
            pocket_expenses = sum(float(a) for k,a,src in funded_rows if src == self.t("my_pocket"))
            owner_expenses = sum(float(a) for k,a,src in funded_rows if src in (self.t("operating_fund"), "Dinero del jefe", "Boss money", "Fondo de operación", "Operating fund"))
            cash_expenses = sum(float(a) for k,a,src in funded_rows if src not in (self.t("my_pocket"), self.t("operating_fund"), "Dinero del jefe", "Boss money", "Fondo de operación", "Operating fund"))
            owner_fund = float(owner_fund_row[0] or 0.0)
            handover = collected - cash_expenses - recovered
            owner_remaining = max(0.0, owner_fund - owner_expenses)
            physical_expected = owner_remaining + handover

            if self.lang == "es":
                summary.text = (
                    f"Viajes registrados: {count}\n"
                    f"Total cobrado: ${collected:.2f}\n"
                    f"Gasolina y otros gastos: ${all_expenses:.2f}\n"
                    f"Gastos pagados con dinero de los viajes: ${cash_expenses:.2f}\n"
                    f"Gastos pagados con dinero personal: ${pocket_expenses:.2f}\n"
                    f"Gastos cubiertos por el propietario: ${owner_expenses:.2f}\n"
                    f"Reembolsos tomados de caja: ${recovered:.2f}\n"
                    f"Fondos recibidos del propietario: ${owner_fund:.2f}\n"
                    f"Saldo del fondo del propietario: ${owner_remaining:.2f}\n"
                    f"Aportes personales pendientes: ${pending:.2f}\n\n"
                    f"GANANCIA NETA: ${net:.2f}\n"
                    f"DINERO DE VIAJES A ENTREGAR: ${handover:.2f}\n"
                    f"EFECTIVO TOTAL A ENTREGAR: ${physical_expected:.2f}"
                )
            else:
                summary.text = (
                    f"Trips recorded: {count}\n"
                    f"Total collected: ${collected:.2f}\n"
                    f"Fuel and other expenses: ${all_expenses:.2f}\n"
                    f"Expenses paid with trip money: ${cash_expenses:.2f}\n"
                    f"Expenses paid with personal money: ${pocket_expenses:.2f}\n"
                    f"Expenses covered by owner: ${owner_expenses:.2f}\n"
                    f"Reimbursements from cash box: ${recovered:.2f}\n"
                    f"Owner funds received: ${owner_fund:.2f}\n"
                    f"Owner fund balance: ${owner_remaining:.2f}\n"
                    f"Personal contributions pending: ${pending:.2f}\n\n"
                    f"NET EARNINGS: ${net:.2f}\n"
                    f"TRIP MONEY TO HAND OVER: ${handover:.2f}\n"
                    f"TOTAL CASH TO HAND OVER: ${physical_expected:.2f}"
                )

        refresh_summary()
        scroll.add_widget(content)
        outer.add_widget(scroll)
        outer.add_widget(self.popup_button(self.t("close"), lambda *_: pop.dismiss(), height=46))
        pop = self.popup(self.t("cash"), outer, (0.94, 0.88))
        pop.open()
    def show_physical_cash(self, *_):
        """Muestra el efectivo esperado en caja y permite compararlo con el conteo físico."""
        day = date.today().isoformat()
        rows = self.day_rows(day)
        count, collected, fuel, other, net = self.totals(rows)
        initial, contributed, recovered, pending = self.cash_totals(day)

        con = sqlite3.connect(DB_PATH)
        funds = con.execute(
            "SELECT source, COALESCE(SUM(amount),0) FROM daily_cash_funds WHERE day=? GROUP BY source",
            (day,)
        ).fetchall()
        funded_rows = con.execute(
            "SELECT m.amount, COALESCE(f.source, ?) FROM movements m "
            "LEFT JOIN movement_funding f ON f.movement_id=m.id "
            "WHERE date(m.created_at)=? AND m.kind IN ('gasolina','otro')",
            (self.t("cash_money"), day)
        ).fetchall()
        con.close()

        owner_sources = (self.t("operating_fund"), "Dinero del jefe", "Boss money", "Fondo de operación", "Operating fund")
        pocket_sources = (self.t("own_money"), "Dinero propio", "Own money", "Fondos personales")
        owner_fund = sum(float(amount) for source, amount in funds if source in owner_sources)
        personal_start = sum(float(amount) for source, amount in funds if source in pocket_sources)
        trip_expenses = sum(float(amount) for amount, source in funded_rows
                            if source not in owner_sources and source not in pocket_sources)
        owner_expenses = sum(float(amount) for amount, source in funded_rows if source in owner_sources)
        owner_remaining = max(0.0, owner_fund - owner_expenses)
        # Los fondos de apertura propios y del dueño forman parte del efectivo físico.
        # Los gastos personales pagados fuera de caja no se restan del efectivo.
        expected = max(0.0, initial - owner_expenses + collected - trip_expenses - recovered)

        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        box.add_widget(self.popup_label("EFECTIVO FÍSICO" if self.lang == "es" else "PHYSICAL CASH", 18, True))
        box.add_widget(self.popup_label(
            f"Fondo de apertura total: ${initial:.2f}\n"
            f"  • Dinero del jefe restante: ${owner_remaining:.2f}\n"
            f"Ingresos de viajes: ${collected:.2f}\n"
            f"Gastos pagados con dinero de viajes: ${trip_expenses:.2f}\n"
            f"Reembolsos pagados desde caja: ${recovered:.2f}", 14
        ))
        box.add_widget(self.popup_label("EFECTIVO ESPERADO EN CAJA" if self.lang == "es" else "EXPECTED CASH IN BOX", 13, True))
        expected_label = self.popup_label(f"${expected:.2f}", 27, True, halign="center")
        box.add_widget(expected_label)
        box.add_widget(self.popup_label("Escribe cuánto dinero contaste físicamente para comparar." if self.lang == "es" else "Enter the cash you physically counted to compare.", 13))
        counted = TextInput(text="", hint_text="Dinero contado (ej. 30.00)", input_filter="float", multiline=False,
                            size_hint_y=None, height=dp(48), font_size=dp(18))
        box.add_widget(counted)
        result = self.popup_label("", 15, True, halign="center")
        box.add_widget(result)
        pop = self.popup("Dinero físico en caja" if self.lang == "es" else "Physical cash in box", box, (0.92, 0.78))
        buttons = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        buttons.add_widget(self.popup_button(self.t("close"), pop.dismiss, height=46))
        def compare(*_):
            try:
                actual = float(counted.text.replace(",", "."))
                if actual < 0:
                    raise ValueError
            except Exception:
                self.message("Dinero físico" if self.lang == "es" else "Physical cash", self.t("invalid_amount"))
                return
            difference = actual - expected
            if abs(difference) < 0.005:
                result.text = "¡Cuadra! No hay diferencia." if self.lang == "es" else "It matches! No difference."
            elif difference < 0:
                result.text = f"Faltan ${abs(difference):.2f}" if self.lang == "es" else f"${abs(difference):.2f} short"
            else:
                result.text = f"Sobran ${difference:.2f}" if self.lang == "es" else f"${difference:.2f} extra"
        buttons.add_widget(self.popup_button("Comparar" if self.lang == "es" else "Compare", compare, primary=True, height=46))
        box.add_widget(buttons)
        pop.open()

    def set_initial_change(self):
        day = date.today().isoformat()
        con = sqlite3.connect(DB_PATH)
        row = con.execute("SELECT initial_change, initial_source FROM daily_cash WHERE day=?", (day,)).fetchone()
        con.close()

        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        box.add_widget(self.popup_label("Agrega una cantidad al fondo de cambio; no reemplaza los aportes anteriores.", 13))
        box.add_widget(self.popup_label(self.t("initial_source"), 13, True))
        source_values = (self.t("own_money"), self.t("operating_fund"))
        current_source = (self.t("own_money") if row and row[1] in ("Dinero propio", "Own money", self.t("own_money")) else self.t("operating_fund"))
        source = Spinner(
            option_cls=GreenSpinnerOption, text=current_source, values=source_values,
            size_hint_y=None, height=dp(46), color=get_color_from_hex(POPUP_TEXT),
            background_normal="", background_color=get_color_from_hex(POPUP_ACCENT)
        )
        box.add_widget(source)
        amount = TextInput(
            text="",
            hint_text=self.t("amount"), input_filter="float", multiline=False,
            size_hint_y=None, height=dp(52),
            foreground_color=get_color_from_hex(POPUP_TEXT),
            background_color=get_color_from_hex(POPUP_FIELD)
        )
        box.add_widget(amount)
        pop = self.popup(self.t("set_change"), box, (0.9, 0.48))
        buttons = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        buttons.add_widget(self.popup_button(self.t("cancel"), pop.dismiss))

        def save(*_):
            try:
                value = float(amount.text.replace(",", "."))
                if value < 0:
                    raise ValueError
            except Exception:
                self.message(self.t("set_change"), self.t("invalid_amount"))
                return
            con = sqlite3.connect(DB_PATH)
            # Sumar el importe al origen elegido sin borrar los fondos anteriores.
            source_name = source.text
            current_fund = con.execute(
                "SELECT amount FROM daily_cash_funds WHERE day=? AND source=?",
                (day, source_name)
            ).fetchone()
            updated_fund = (float(current_fund[0]) if current_fund else 0.0) + value
            con.execute(
                """INSERT INTO daily_cash_funds(day, source, amount) VALUES(?,?,?)
                   ON CONFLICT(day, source) DO UPDATE SET amount=excluded.amount""",
                (day, source_name, updated_fund)
            )
            total_initial = con.execute(
                "SELECT COALESCE(SUM(amount),0) FROM daily_cash_funds WHERE day=?",
                (day,)
            ).fetchone()[0]
            con.execute(
                """INSERT INTO daily_cash(day, initial_change, initial_source)
                   VALUES(?,?,?)
                   ON CONFLICT(day) DO UPDATE SET
                   initial_change=excluded.initial_change,
                   initial_source=excluded.initial_source""",
                (day, float(total_initial), source_name)
            )
            # Solo el dinero propio se contabiliza como aporte personal recuperable.
            if source_name in (self.t("own_money"), "Dinero propio", "Own money") and value > 0:
                con.execute(
                    """INSERT INTO personal_contributions
                       (day, amount, category, detail, recovered, created_at)
                       VALUES(?,?,?,?,0,?)""",
                    (day, value, "cambio_inicial",
                     "Cambio inicial agregado con dinero propio",
                     datetime.now().isoformat(timespec="seconds"))
                )
            con.commit()
            con.close()

            # Actualizar la tarjeta de Inicio inmediatamente con el valor recién guardado.
            if "initial_tile" in getattr(self, "metric_labels", {}):
                self.metric_labels["initial_tile"].text = f"${value:.2f}"
            pop.dismiss()
            self.update_screen()

            # Refrescar la ventana Caja con el dato persistido en SQLite.
            from kivy.clock import Clock
            Clock.schedule_once(lambda *_: self.show_cash(), 0.15)

        buttons.add_widget(self.popup_button(self.t("save"), save, primary=True))
        box.add_widget(buttons)
        pop.open()

    def register_recovery(self):
        day = date.today().isoformat()
        initial, contributed, recovered, pending = self.cash_totals(day)
        if pending <= 0:
            self.message(self.t("cash"), self.t("no_pending")); return
        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        box.add_widget(self.popup_label(f"{self.t('pending_recovery')}: ${pending:.2f}", 15, True))
        amount = TextInput(text=f"{pending:.2f}", hint_text=self.t("recovery_amount"), input_filter="float", multiline=False, size_hint_y=None, height=dp(52))
        box.add_widget(amount)
        pop = self.popup(self.t("register_recovery"), box, (0.9, 0.4))
        buttons = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        buttons.add_widget(self.popup_button(self.t("cancel"), pop.dismiss))
        def save(*_):
            try:
                value = float(amount.text.replace(",", "."))
                if value <= 0 or value > pending + 0.0001: raise ValueError
            except Exception:
                self.message(self.t("register_recovery"), self.t("invalid_amount")); return
            con = sqlite3.connect(DB_PATH)
            rows = con.execute("SELECT id,amount,recovered FROM personal_contributions WHERE day=? AND recovered<amount ORDER BY id", (day,)).fetchall()
            remaining = value
            for rid, total, already in rows:
                available = float(total) - float(already)
                take = min(available, remaining)
                if take > 0:
                    con.execute("UPDATE personal_contributions SET recovered=recovered+? WHERE id=?", (take, rid))
                    remaining -= take
                if remaining <= 0.0001: break
            con.commit(); con.close(); pop.dismiss(); self.update_screen(); self.show_cash()
        buttons.add_widget(self.popup_button(self.t("save"), save, primary=True))
        box.add_widget(buttons); pop.open()

    def show_history(self, *_):
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        date_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        date_in = TextInput(text=date.today().isoformat(), readonly=True, multiline=False, size_hint_x=0.62)
        date_row.add_widget(date_in); date_row.add_widget(self.button(self.t("choose_date"), lambda *_: self.choose_date(date_in.text, lambda v: (setattr(date_in,"text",v), load())), height=46, font_size=12))
        box.add_widget(date_row)
        summary = self.popup_label("", 13, True)
        box.add_widget(summary)
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(4))
        list_box = GridLayout(cols=1, spacing=dp(7), size_hint_y=None, padding=(0,dp(4)))
        list_box.bind(minimum_height=list_box.setter("height")); scroll.add_widget(list_box); box.add_widget(scroll)
        footer = BoxLayout(size_hint_y=None, height=dp(48)); footer.add_widget(self.popup_button(self.t("close"), lambda *_: pop.dismiss(), height=48))
        box.add_widget(footer)
        pop = self.popup(self.t("history"), box, (0.96, 0.92))
        def load(*_):
            list_box.clear_widgets()
            try: datetime.strptime(date_in.text.strip(), "%Y-%m-%d")
            except Exception: summary.text=self.t("invalid_date"); return
            rows = self.day_rows(date_in.text.strip())
            c,t,g,o,n = self.totals(rows)
            summary.text = f"{self.t('trips')}: {c}  |  {self.t('collected')}: ${t:.2f}  |  {self.t('net')}: ${n:.2f}"
            if not rows:
                list_box.add_widget(self.popup_label(self.t("no_movements"), 14, size_hint_y=None, height=dp(65)))
                return
            trip_no=0
            for rid,kind,amount,detail,ts in rows:
                if kind == "viaje": trip_no += 1; name=f"{self.t('trip')} {trip_no}"; sign="+"; col=self.colors["primary"]
                elif kind == "gasolina": name=self.t("fuel_title"); sign="−"; col=self.colors["danger"]
                else: name=detail or self.t("other"); sign="−"; col="#E8A23A"
                tm=datetime.strptime(ts,"%Y-%m-%d %H:%M:%S").strftime("%I:%M %p")
                row=BoxLayout(size_hint_y=None,height=dp(66),spacing=dp(7),padding=(dp(8),dp(5)))
                from kivy.graphics import Color, RoundedRectangle
                with row.canvas.before:
                    Color(*get_color_from_hex(self.colors["surface"]))
                    row._rr=RoundedRectangle(pos=row.pos,size=row.size,radius=[dp(12)])
                row.bind(pos=lambda w,p: setattr(w._rr,"pos",p),size=lambda w,s: setattr(w._rr,"size",s))
                details=BoxLayout(orientation="vertical",spacing=dp(2))
                details.add_widget(self.popup_label(name,14,True,halign="left")); details.add_widget(self.popup_label(tm,11,halign="left"))
                row.add_widget(details); row.add_widget(self.label(f"{sign}${amount:.2f}",14,True,col,size_hint_x=0.36))
                actions=Spinner(option_cls=GreenSpinnerOption, text="...", values=(self.t("edit"),self.t("delete")), size_hint_x=None,width=dp(45),height=dp(42), color=get_color_from_hex(POPUP_TEXT), background_normal="", background_color=get_color_from_hex(POPUP_ACCENT))
                def action(sp, value, rid=rid, kind=kind, amount=amount, detail=detail):
                    sp.text="..."
                    if value==self.t("edit"):
                        self.form_popup(self.t("edit_movement"),kind,existing=(amount,detail,rid),on_saved=load)
                    elif value==self.t("delete"):
                        self.confirm_delete(rid,load)
                actions.bind(text=lambda sp,val: action(sp,val) if val in (self.t("edit"),self.t("delete")) else None)
                row.add_widget(actions); list_box.add_widget(row)
        pop.open(); load()

    def confirm_delete(self, rid, refresh):
        box=BoxLayout(orientation="vertical",padding=dp(14),spacing=dp(12)); box.add_widget(self.popup_label(self.t("confirm_delete"),15))
        pop=self.popup(self.t("delete"), box, (0.86, 0.32))
        buttons=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(8))
        buttons.add_widget(self.popup_button(self.t("cancel"),pop.dismiss))
        def delete(*_):
            try:
                self.backup_database()
            except Exception:
                self.message(self.t("backup"), self.t("backup_error")); return
            con=sqlite3.connect(DB_PATH)
            linked = con.execute("SELECT id,recovered FROM personal_contributions WHERE movement_id=?", (rid,)).fetchall()
            if any(float(row[1]) > 0.0001 for row in linked):
                con.close()
                self.message(self.t("delete"), "No puedes borrar este gasto porque ya tiene una recuperación registrada.")
                return
            con.execute("DELETE FROM personal_contributions WHERE movement_id=?", (rid,))
            con.execute("DELETE FROM movement_funding WHERE movement_id=?", (rid,))
            con.execute("DELETE FROM movements WHERE id=?", (rid,))
            con.commit(); con.close(); pop.dismiss(); self.update_screen(); refresh()
        buttons.add_widget(self.button(self.t("delete"),delete,self.colors["danger"],"#FFFFFF")); box.add_widget(buttons); pop.open()

    def choose_date(self, initial, callback):
        box=BoxLayout(orientation="vertical",padding=dp(12),spacing=dp(8))
        inp=TextInput(text=initial,multiline=False,size_hint_y=None,height=dp(48),foreground_color=get_color_from_hex(POPUP_TEXT),background_color=get_color_from_hex(POPUP_FIELD),cursor_color=get_color_from_hex(POPUP_GREEN))
        box.add_widget(self.popup_label(f"{self.t('date')}: YYYY-MM-DD",13)); box.add_widget(inp)
        pop=self.popup(self.t("choose_date"), box, (0.88, 0.36))
        buttons=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(8))
        buttons.add_widget(self.popup_button(self.t("cancel"),pop.dismiss))
        def use(*_):
            try: datetime.strptime(inp.text.strip(),"%Y-%m-%d")
            except Exception: self.message(self.t("choose_date"),self.t("invalid_date")); return
            callback(inp.text.strip()); pop.dismiss()
        buttons.add_widget(self.popup_button(self.t("show"),use,primary=True)); box.add_widget(buttons); pop.open()

    def preset_dates(self, mode):
        today=date.today()
        if mode=="today": return today,today
        if mode=="yesterday": d=today-timedelta(days=1); return d,d
        if mode=="week":
            monday=today-timedelta(days=today.weekday())
            return monday,monday+timedelta(days=6)
        if mode=="last_week": monday=today-timedelta(days=today.weekday()+7); return monday,monday+timedelta(days=6)
        if mode=="month": return today.replace(day=1),today
        return today,today

    def get_day_status(self, day):
        con=sqlite3.connect(DB_PATH)
        row=con.execute("SELECT status FROM day_status WHERE day=?",(day,)).fetchone()
        con.close()
        return row[0] if row else None

    def set_day_status(self, day, status):
        con=sqlite3.connect(DB_PATH)
        con.execute("INSERT INTO day_status(day,status,updated_at) VALUES(?,?,?) ON CONFLICT(day) DO UPDATE SET status=excluded.status,updated_at=excluded.updated_at",(day,status,datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        con.commit(); con.close()

    def show_day_status(self, *_):
        box=BoxLayout(orientation="vertical",padding=dp(14),spacing=dp(9))
        day=TextInput(text=date.today().isoformat(),readonly=True,multiline=False,size_hint_y=None,height=dp(42),foreground_color=get_color_from_hex(POPUP_TEXT),background_color=get_color_from_hex(POPUP_FIELD))
        box.add_widget(self.popup_label(self.t("date"),12,True)); box.add_widget(day)
        box.add_widget(self.popup_button(self.t("choose_date"),lambda *_: self.choose_date(day.text,lambda v:setattr(day,"text",v)),height=42))
        status_values=(self.t("worked"),self.t("not_worked"),self.t("rest_day"))
        status_map={self.t("worked"):"worked",self.t("not_worked"):"not_worked",self.t("rest_day"):"rest_day"}
        shown={"worked":self.t("worked"),"not_worked":self.t("not_worked"),"rest_day":self.t("rest_day")}
        picker=Spinner(option_cls=GreenSpinnerOption,text=shown.get(self.get_day_status(day.text),status_values[0]),values=status_values,size_hint_y=None,height=dp(46),color=get_color_from_hex(POPUP_TEXT),background_normal="",background_color=get_color_from_hex(POPUP_ACCENT))
        box.add_widget(self.popup_label(self.t("day_status"),12,True)); box.add_widget(picker)
        pop=self.popup(self.t("day_status"),box,(0.9,0.52))
        buttons=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(8))
        buttons.add_widget(self.popup_button(self.t("cancel"),pop.dismiss))
        def save(*_):
            try: datetime.strptime(day.text.strip(),"%Y-%m-%d")
            except Exception: self.message(self.t("day_status"),self.t("invalid_date")); return
            self.set_day_status(day.text.strip(),status_map[picker.text]); pop.dismiss()
            self.message(self.t("day_status"),self.t("status_saved"))
        buttons.add_widget(self.popup_button(self.t("save"),save,primary=True)); box.add_widget(buttons)
        def refresh_status(*_): picker.text=shown.get(self.get_day_status(day.text),status_values[0])
        day.bind(text=refresh_status)
        pop.open()

    def show_reports(self, *_):
        box=BoxLayout(orientation="vertical",padding=dp(12),spacing=dp(8))
        preset_values=(self.t("today_preset"),self.t("yesterday"),self.t("this_week"),self.t("last_week"),self.t("this_month"),self.t("custom"))
        preset=Spinner(option_cls=GreenSpinnerOption, text=preset_values[0],values=preset_values,size_hint_y=None,height=dp(46),color=get_color_from_hex(POPUP_TEXT),background_normal="",background_color=get_color_from_hex(POPUP_ACCENT))
        start=TextInput(text=date.today().isoformat(),readonly=True,size_hint_y=None,height=dp(42),foreground_color=get_color_from_hex(POPUP_TEXT),background_color=get_color_from_hex(POPUP_FIELD))
        end=TextInput(text=date.today().isoformat(),readonly=True,size_hint_y=None,height=dp(42),foreground_color=get_color_from_hex(POPUP_TEXT),background_color=get_color_from_hex(POPUP_FIELD))
        info=self.popup_label(self.t("period"),13)
        gen=self.button(self.t("generate_pdf"),lambda *_: generate(),self.colors["primary"],self.colors["primary_text"],52)
        share=self.button(self.t("share_pdf"),lambda *_: self.share_pdf(getattr(share,"path",None)),height=48); share.disabled=True
        close=self.button(self.t("close"),lambda *_: pop.dismiss(),height=44)
        status_button=self.button(self.t("day_status"),self.show_day_status,height=42,font_size=12)
        for w in (preset,self.popup_label(self.t("start_date"),12),start,self.button(self.t("choose_date"),lambda *_: self.choose_date(start.text,lambda v:setattr(start,"text",v)),height=42),self.popup_label(self.t("end_date"),12),end,self.button(self.t("choose_date"),lambda *_: self.choose_date(end.text,lambda v:setattr(end,"text",v)),height=42),status_button,info,gen,share,close): box.add_widget(w)
        pop=self.popup(self.t("reports"), box, (0.94, 0.94))
        mode_map={preset_values[0]:"today",preset_values[1]:"yesterday",preset_values[2]:"week",preset_values[3]:"last_week",preset_values[4]:"month"}
        def apply(*_):
            if preset.text in mode_map:
                a,b=self.preset_dates(mode_map[preset.text]); start.text=a.isoformat(); end.text=b.isoformat()
        def generate():
            try:
                d1=datetime.strptime(start.text.strip(),"%Y-%m-%d").date(); d2=datetime.strptime(end.text.strip(),"%Y-%m-%d").date()
                if d2<d1: raise ValueError
            except Exception: info.text=self.t("check_dates"); return
            if not REPORTLAB_OK: info.text=self.t("need_reportlab"); return
            try:
                share.path=self.make_pdf(d1,d2); share.disabled=False; info.text=self.t("pdf_created")
            except Exception as exc: info.text=f"{self.t('need_reportlab')} ({exc})"
        preset.bind(text=lambda *_: apply()); pop.open()

    def make_pdf(self,d1,d2):
        # Reporte con ingresos brutos, ambos tipos de gastos, ganancia neta y saldo físico.
        # El saldo físico es un saldo, no una cantidad que se sume entre días.
        from reportlab.lib.pagesizes import landscape
        out=Path(self.user_data_dir)/f"taxpanda_report_{d1}_{d2}.pdf"
        c=canvas.Canvas(str(out),pagesize=landscape(letter))
        W,H=landscape(letter)
        green=(0.08,0.42,0.25); dark=(0.15,0.17,0.16); pale=(0.88,0.94,0.90)
        weekdays_es=["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
        weekdays_en=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        daily=[]; cur=d1; total_trips=0
        status_labels={"worked":self.t("worked"),"not_worked":self.t("not_worked"),"rest_day":self.t("rest_day")}
        owner_sources=(self.t("operating_fund"), "Dinero del jefe", "Boss money", "Fondo de operación", "Operating fund")
        pocket_sources=(self.t("own_money"), "Dinero propio", "Own money", "Fondos personales")
        while cur<=d2:
            day=cur.isoformat(); rows=self.day_rows(day)
            count,collected,fuel,other,net=self.totals(rows)
            saved_status=self.get_day_status(day)
            if saved_status in status_labels: status=status_labels[saved_status]
            elif count>0: status=self.t("worked")
            elif cur>date.today(): status=self.t("pending_day")
            elif rows: status="Sin viajes" if self.lang=="es" else "No trips"
            else: status=self.t("unregistered")

            # Calcular efectivo disponible con la misma regla que la tarjeta principal.
            initial, contributed, recovered, pending = self.cash_totals(day)
            con=sqlite3.connect(DB_PATH)
            funds=con.execute("SELECT source, COALESCE(SUM(amount),0) FROM daily_cash_funds WHERE day=? GROUP BY source",(day,)).fetchall()
            funded=con.execute("SELECT m.amount, COALESCE(f.source, ?) FROM movements m LEFT JOIN movement_funding f ON f.movement_id=m.id WHERE date(m.created_at)=? AND m.kind IN ('gasolina','otro')",(self.t("cash_money"),day)).fetchall()
            con.close()
            owner_fund=sum(float(a) for src,a in funds if src in owner_sources)
            owner_expenses=sum(float(a) for a,src in funded if src in owner_sources)
            trip_expenses=sum(float(a) for a,src in funded if src not in owner_sources and src not in pocket_sources)
            physical=max(0.0, collected-trip_expenses-recovered+max(0.0,owner_fund-owner_expenses))
            daily.append({"date":cur,"count":count,"collected":collected,"fuel":fuel,"other":other,"net":net,"physical":physical,"status":status,
                          "initial":initial,"contributed":contributed,"recovered":recovered,
                          "owner_fund":owner_fund,"owner_expenses":owner_expenses,
                          "trip_expenses":trip_expenses})
            total_trips+=count; cur+=timedelta(days=1)

        margin=28; table_width=W-2*margin
        widths=[table_width*0.34,table_width*0.16,table_width*0.15,table_width*0.15,table_width*0.20]
        row_h=31; y=H-42
        def header(title=True):
            nonlocal y
            c.setFillColorRGB(*green); c.setFont("Helvetica-Bold",20)
            c.drawCentredString(W/2,y,"TAXPANDA - REPORTE" if self.lang=="es" else "TAXPANDA - REPORT")
            y-=25; c.setFillColorRGB(*dark); c.setFont("Helvetica",10)
            c.drawCentredString(W/2,y,("Período" if self.lang=="es" else "Period")+f": {d1.strftime('%d/%m/%Y')} - {d2.strftime('%d/%m/%Y')}")
            y-=28
            labels=( ["Día","Total bruto","Gasolina","Otros gastos","Ganancia neta"] if self.lang=="es" else ["Day","Gross total","Fuel","Other expenses","Net earnings"] )
            c.setFillColorRGB(*green); c.rect(margin,y-row_h,table_width,row_h,fill=1,stroke=0)
            c.setFillColorRGB(1,1,1); c.setFont("Helvetica-Bold",9)
            x=margin
            for label,width in zip(labels,widths): c.drawCentredString(x+width/2,y-20,label); x+=width
            y-=row_h
        header()
        total_collected=total_fuel=total_other=total_net=0.0; best=None
        last_physical=0.0; last_day=None
        for idx,item in enumerate(daily):
            if y<92:
                c.showPage(); y=H-42; header()
            if idx%2==0:
                c.setFillColorRGB(0.95,0.97,0.95); c.rect(margin,y-row_h,table_width,row_h,fill=1,stroke=0)
            c.setFillColorRGB(*dark); c.setFont("Helvetica",8)
            daynames=weekdays_es if self.lang=="es" else weekdays_en
            day_label=f"{daynames[item['date'].weekday()]} {item['date'].strftime('%d/%m/%Y')}"
            vals=[day_label,f"${item['collected']:.2f}",f"${item['fuel']:.2f}",f"${item['other']:.2f}",f"${item['net']:.2f}"]
            x=margin
            for col,(value,width) in enumerate(zip(vals,widths)):
                if col==0: c.drawString(x+7,y-20,value)
                else: c.drawCentredString(x+width/2,y-20,value)
                x+=width
            y-=row_h
            total_collected+=item['collected']; total_fuel+=item['fuel']; total_other+=item['other']; total_net+=item['net']
            if best is None or item['collected']>best['collected']: best=item
            if last_day is None or item['date']>=last_day:
                last_day=item['date']; last_physical=item['physical']
        y-=10
        # Recuadro integrado: totales y conciliación del efectivo en una sola tarjeta.
        card_h=105
        if y-card_h < 45:
            c.showPage(); y=H-48
        c.setFillColorRGB(*pale); c.roundRect(margin,y-card_h,table_width,card_h,7,fill=1,stroke=0)
        c.setFillColorRGB(*green); c.setFont("Helvetica-Bold",10)
        c.drawString(margin+8,y-18,"TOTAL" if self.lang=="es" else "TOTAL")
        totals=[total_collected,total_fuel,total_other,total_net]
        x=margin+widths[0]
        for amount,width in zip(totals,widths[1:]):
            c.drawCentredString(x+width/2,y-18,f"${amount:.2f}"); x+=width
        closing = next((item for item in daily if item["date"] == last_day), None)
        c.setStrokeColorRGB(0.72,0.83,0.75); c.line(margin+8,y-27,margin+table_width-8,y-27)
        c.setFillColorRGB(*green); c.setFont("Helvetica-Bold",10)
        cash_label=(f"DINERO FÍSICO AL CIERRE: ${last_physical:.2f}" if self.lang=="es" else f"PHYSICAL CASH AT CLOSE: ${last_physical:.2f}")
        c.drawString(margin+8,y-42,cash_label)
        if closing:
            c.setFillColorRGB(*dark); c.setFont("Helvetica",8)
            if self.lang=="es":
                details=(f"Ingresos: ${closing['collected']:.2f}  |  Gastos de viajes: -${closing['trip_expenses']:.2f}  |  Reembolsos de caja: -${closing['recovered']:.2f}",
                         f"Fondo de apertura: ${closing['initial']:.2f}  |  Fondo del jefe restante: ${max(0.0, closing['owner_fund']-closing['owner_expenses']):.2f}  |  Aportes pendientes: ${max(0.0, closing['contributed']-closing['recovered']):.2f}")
            else:
                details=(f"Income: ${closing['collected']:.2f}  |  Trip expenses: -${closing['trip_expenses']:.2f}  |  Cash reimbursements: -${closing['recovered']:.2f}",
                         f"Opening fund: ${closing['initial']:.2f}  |  Owner's remaining fund: ${max(0.0, closing['owner_fund']-closing['owner_expenses']):.2f}  |  Pending contributions: ${max(0.0, closing['contributed']-closing['recovered']):.2f}")
            c.drawString(margin+8,y-58,details[0])
            c.drawString(margin+8,y-72,details[1])
        c.setFillColorRGB(*dark); c.setFont("Helvetica",9)
        c.drawString(margin,y-card_h-17,(f"Viajes incluidos: {total_trips}" if self.lang=="es" else f"Trips included: {total_trips}"))
        y-=card_h+30
        if best:
            if y < 35:
                c.showPage(); y=H-45
            daynames=weekdays_es if self.lang=="es" else weekdays_en
            best_label=f"{daynames[best['date'].weekday()]} {best['date'].strftime('%d/%m/%Y')}"
            best_text=(f"Mejor día por cobro: {best_label} (${best['collected']:.2f})" if self.lang=="es" else f"Best day by collection: {best_label} (${best['collected']:.2f})")
            c.setFont("Helvetica",9); c.setFillColorRGB(*dark); c.drawString(margin,y,best_text)
        c.save()
        self.last_pdf_uri=None
        if ANDROID_OK:
            try: self.last_pdf_uri=self.publish_pdf_to_downloads(str(out))
            except Exception: self.last_pdf_uri=None
        return str(out)

    def publish_pdf_to_downloads(self,path):
        PythonActivity=autoclass("org.kivy.android.PythonActivity"); ContentValues=autoclass("android.content.ContentValues")
        MediaColumns=autoclass("android.provider.MediaStore$MediaColumns"); Downloads=autoclass("android.provider.MediaStore$Downloads"); Environment=autoclass("android.os.Environment")
        activity=PythonActivity.mActivity; resolver=activity.getContentResolver(); values=ContentValues()
        values.put(MediaColumns.DISPLAY_NAME,Path(path).name); values.put(MediaColumns.MIME_TYPE,"application/pdf")
        values.put(MediaColumns.RELATIVE_PATH,Environment.DIRECTORY_DOWNLOADS+"/Mi Trabajo")
        uri=resolver.insert(Downloads.EXTERNAL_CONTENT_URI,values)
        if uri is None: raise RuntimeError("Android could not create the PDF")
        try:
            output=resolver.openOutputStream(uri)
            with open(path,"rb") as source:
                while True:
                    chunk=source.read(65536)
                    if not chunk: break
                    output.write(bytearray(chunk))
            output.close(); return uri
        except Exception:
            try: resolver.delete(uri,None,None)
            except Exception: pass
            raise

    def share_pdf(self,path):
        if not path: return
        if ANDROID_OK:
            try:
                PythonActivity=autoclass("org.kivy.android.PythonActivity"); Intent=autoclass("android.content.Intent")
                uri=getattr(self,"last_pdf_uri",None) or self.publish_pdf_to_downloads(path)
                intent=Intent(Intent.ACTION_SEND); intent.setType("application/pdf")
                intent.putExtra(Intent.EXTRA_STREAM,cast("android.os.Parcelable",uri)); intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                PythonActivity.mActivity.startActivity(intent); return
            except Exception: self.message(self.t("share_pdf"),self.t("share_error")); return
        self.message(self.t("share_pdf"),str(path))


    def reset_test_records(self, *_):
        """Borra movimientos y datos de caja, pero conserva preferencias y esquema."""
        box = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(14))
        message = self.popup_label(self.t("reset_confirm"), 14, halign="left", valign="middle")
        message.size_hint_y = 1
        message.bind(size=lambda inst, value: setattr(inst, "text_size", (value[0], None)))
        box.add_widget(message)

        pop = self.popup(self.t("reset_test_data"), box, (0.92, 0.42))
        buttons = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        buttons.add_widget(self.popup_button(self.t("cancel"), pop.dismiss, height=48, font_size=13))

        def confirm(*_):
            con = None
            try:
                self.backup_database()
                con = sqlite3.connect(DB_PATH)
                con.execute("DELETE FROM movements")
                con.execute("DELETE FROM movement_funding")
                con.execute("DELETE FROM personal_contributions")
                con.execute("DELETE FROM daily_cash")
                con.execute("DELETE FROM daily_cash_funds")
                con.execute("DELETE FROM day_status")
                con.commit()
                con.close()
            except Exception:
                if con:
                    con.close()
                self.message(self.t("reset_test_data"), self.t("reset_error"))
                return
            pop.dismiss()
            # Actualiza las etiquetas que ya están visibles en Inicio.
            # Reconstruir show_home() aquí reemplazaba las referencias de las
            # etiquetas sin sustituir la raíz visible, por eso los datos viejos
            # permanecían hasta cerrar y volver a abrir la app.
            self.update_screen()
            self.message(self.t("reset_test_data"), self.t("reset_done"))

        short_confirm = "Reiniciar" if self.lang == "es" else "Reset"
        buttons.add_widget(self.popup_button(short_confirm, confirm, primary=True, height=48, font_size=13))
        box.add_widget(buttons)
        pop.open()

    def show_settings(self, *_):
        # El contenido completo queda dentro de un área desplazable en móviles.
        outer = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(8))
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(3))
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10), size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))

        box.add_widget(self.popup_label(self.t("language"), 14, True))
        language = Spinner(option_cls=GreenSpinnerOption,
            text=self.t("spanish") if self.lang == "es" else self.t("english"),
            values=(self.t("spanish"), self.t("english")), size_hint_y=None, height=dp(46),
            color=get_color_from_hex(POPUP_TEXT), background_normal="",
            background_color=get_color_from_hex(POPUP_ACCENT))
        box.add_widget(language)
        box.add_widget(self.popup_label(self.t("appearance"), 14, True))
        theme = Spinner(option_cls=GreenSpinnerOption,
            text=self.t("day_mode") if self.theme_name == "day" else self.t("night_mode"),
            values=(self.t("day_mode"), self.t("night_mode")), size_hint_y=None, height=dp(46),
            color=get_color_from_hex(POPUP_TEXT), background_normal="",
            background_color=get_color_from_hex(POPUP_ACCENT))
        box.add_widget(theme)
        box.add_widget(self.popup_button(self.t("create_backup"), lambda *_: self.show_backup(), height=46, font_size=13))
        box.add_widget(self.popup_button(self.t("restore_backup"), lambda *_: self.show_restore_backup(), height=46, font_size=13))
        box.add_widget(self.button(self.t("reset_test_data"), self.reset_test_records,
                                   self.colors["danger"], "#FFFFFF", 46, 12))
        scroll.add_widget(box)
        outer.add_widget(scroll)

        pop = self.popup(self.t("settings"), outer, (0.92, 0.78))
        buttons = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        buttons.add_widget(self.popup_button(self.t("close"), pop.dismiss, height=48, font_size=13))

        def save(*_):
            self.lang = "es" if language.text in ("Español", "Spanish") else "en"
            self.theme_name = "day" if theme.text in ("Modo día", "Day mode") else "night"
            self.save_preferences()
            pop.dismiss()
            self.show_home()

        buttons.add_widget(self.popup_button(self.t("save_settings"), save, primary=True, height=48, font_size=11))
        outer.add_widget(buttons)
        pop.open()

    def backup_database(self):
        """Crea una copia consistente de la base de datos sin modificar el original."""
        if not DB_PATH.exists():
            raise FileNotFoundError("No se encontró la base de datos original.")
        folder = Path(self.user_data_dir) / "backups"
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        dest = folder / f"taxpanda_backup_{stamp}.db"
        try:
            with sqlite3.connect(str(DB_PATH)) as source:
                with sqlite3.connect(str(dest)) as target:
                    source.backup(target)
            with sqlite3.connect(str(dest)) as check:
                result = check.execute("PRAGMA integrity_check").fetchone()
                if not result or result[0] != "ok":
                    raise sqlite3.DatabaseError("La copia no superó la comprobación de integridad.")
            return str(dest)
        except Exception:
            try:
                dest.unlink(missing_ok=True)
            except Exception:
                pass
            raise

    def show_backup(self,*_):
        try: path=self.backup_database(); self.message(self.t("backup"),f"{self.t('backup_done')}\n\n{path}\n\n{self.t('edit_backup_note')}")
        except Exception: self.message(self.t("backup"),self.t("backup_error"))

    def available_backups(self):
        folder = Path(self.user_data_dir) / "backups"
        if not folder.exists():
            return []
        return sorted(folder.glob("taxpanda_backup_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)

    def show_restore_backup(self, *_):
        backups = self.available_backups()
        if not backups:
            self.message(self.t("restore_backup"), self.t("restore_none"))
            return
        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        box.add_widget(self.popup_label(self.t("restore_backup"), 16, True))
        options = [f"{p.name}  ({datetime.fromtimestamp(p.stat().st_mtime).strftime('%d/%m/%Y %H:%M')})" for p in backups]
        chooser = Spinner(option_cls=GreenSpinnerOption, text=options[0], values=options,
                          size_hint_y=None, height=dp(52), color=get_color_from_hex(POPUP_TEXT),
                          background_normal="", background_color=get_color_from_hex(POPUP_ACCENT))
        box.add_widget(chooser)
        box.add_widget(self.popup_label(self.t("restore_confirm"), 13))
        pop = self.popup(self.t("restore_backup"), box, (0.94, 0.58))
        buttons = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        buttons.add_widget(self.popup_button(self.t("cancel"), pop.dismiss))
        def confirm(*_):
            selected = options.index(chooser.text)
            source = backups[selected]
            pop.dismiss()
            self.confirm_restore_backup(source)
        buttons.add_widget(self.popup_button(self.t("restore_backup"), confirm, primary=True, height=48, font_size=12))
        box.add_widget(buttons)
        pop.open()

    def confirm_restore_backup(self, source):
        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        box.add_widget(self.popup_label(self.t("restore_confirm"), 14, True))
        pop = self.popup(self.t("restore_backup"), box, (0.9, 0.42))
        buttons = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        buttons.add_widget(self.popup_button(self.t("cancel"), pop.dismiss))
        def restore(*_):
            try:
                # Validate source before touching the current database.
                with sqlite3.connect(str(source)) as check:
                    integrity = check.execute("PRAGMA integrity_check").fetchone()
                    tables = {r[0] for r in check.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                    if not integrity or integrity[0] != "ok" or "movements" not in tables:
                        raise sqlite3.DatabaseError("Copia no válida")
                    columns = {r[1] for r in check.execute("PRAGMA table_info(movements)")}
                    if not {"id", "kind", "amount", "detail", "created_at"}.issubset(columns):
                        raise sqlite3.DatabaseError("Esquema incompatible")
                # Keep a safety copy of the current database before restoration.
                self.backup_database()
                temp = DB_PATH.with_name("mi_trabajo_restore_tmp.db")
                shutil.copy2(str(source), str(temp))
                with sqlite3.connect(str(temp)) as check:
                    integrity = check.execute("PRAGMA integrity_check").fetchone()
                    if not integrity or integrity[0] != "ok":
                        raise sqlite3.DatabaseError("Copia temporal dañada")
                # Atomic replacement prevents a partially copied database.
                temp.replace(DB_PATH)
                # Recreate any new Taxpanda tables when restoring an older backup.
                self.create_db()
                pop.dismiss()
                self.show_home()
                self.message(self.t("restore_backup"), self.t("restore_done"))
            except Exception:
                try:
                    temp_path = DB_PATH.with_name("mi_trabajo_restore_tmp.db")
                    if temp_path.exists(): temp_path.unlink()
                except Exception:
                    pass
                pop.dismiss()
                self.message(self.t("restore_backup"), self.t("restore_error"))
        buttons.add_widget(self.popup_button(self.t("restore_backup"), restore, primary=True, height=48, font_size=12))
        box.add_widget(buttons)
        pop.open()

    def message(self,title,text):
        box=BoxLayout(orientation="vertical",padding=dp(14),spacing=dp(10)); box.add_widget(self.popup_label(text,14))
        pop=self.popup(title, box, (0.9, 0.4))
        box.add_widget(self.popup_button(self.t("close"),pop.dismiss)); pop.open()

if __name__ == "__main__":
    TaxpandaApp().run()
