__version__ = "1.0.0"
# -*- coding: utf-8 -*-
import sqlite3
import shutil
from datetime import datetime, date, timedelta
from pathlib import Path

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.core.window import Window

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False

try:
    from jnius import autoclass
    ANDROID_OK = True
except Exception:
    ANDROID_OK = False

DB_PATH = Path(__file__).with_name("mi_trabajo.db")


class MiTrabajoApp(App):
    def build(self):
        self.title = "Mi Trabajo"
        self.create_db()

        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(9))

        header = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(8))
        title = Label(text="MI TRABAJO", font_size=dp(23), bold=True,
                      halign="left", valign="middle")
        self.clock = Label(font_size=dp(13), halign="right", valign="middle")
        header.add_widget(title)
        header.add_widget(self.clock)
        root.add_widget(header)

        self.trip_btn = self.make_button("+ VIAJE", (0.04, 0.67, 0.28, 1), 76, self.add_trip)
        self.gas_btn = self.make_button("GASOLINA", (0.90, 0.16, 0.16, 1), 70, self.add_gas)
        self.other_btn = self.make_button("OTRO GASTO", (0.96, 0.48, 0.05, 1), 70, self.add_other)
        root.add_widget(self.trip_btn)
        root.add_widget(self.gas_btn)
        root.add_widget(self.other_btn)

        self.summary = Label(font_size=dp(16), halign="left", valign="middle")
        root.add_widget(self.summary)

        nav = GridLayout(cols=3, size_hint_y=None, height=dp(52), spacing=dp(6))
        for text, fn in [
            ("HISTORIAL", self.show_history),
            ("REPORTES PDF", self.show_reports),
            ("COPIA", self.show_backup)
        ]:
            b = Button(text=text, font_size=dp(13))
            b.bind(on_release=fn)
            nav.add_widget(b)
        root.add_widget(nav)

        self.root_layout = root
        self.update_screen()
        return root

    def make_button(self, text, color, height, callback):
        b = Button(text=text, font_size=dp(20), bold=True,
                   size_hint_y=None, height=dp(height),
                   background_normal="", background_color=color)
        b.bind(on_release=callback)
        return b

    def create_db(self):
        con = sqlite3.connect(DB_PATH)
        con.execute("""
            CREATE TABLE IF NOT EXISTS movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                amount REAL NOT NULL,
                detail TEXT,
                created_at TEXT NOT NULL
            )
        """)
        con.commit()
        con.close()

    def next_trip_number(self, day=None):
        day = day or date.today().isoformat()
        con = sqlite3.connect(DB_PATH)
        n = con.execute(
            "SELECT COUNT(*) FROM movements WHERE kind='viaje' AND date(created_at)=?",
            (day,)
        ).fetchone()[0]
        con.close()
        return n + 1

    def save_movement(self, kind, amount, detail=""):
        con = sqlite3.connect(DB_PATH)
        con.execute(
            "INSERT INTO movements(kind,amount,detail,created_at) VALUES(?,?,?,?)",
            (kind, amount, detail, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        con.commit()
        con.close()
        self.update_screen()

    def money_popup(self, title, kind, trip_number=None, choices=None):
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(9))

        if trip_number:
            top = Label(text=f"VIAJE {trip_number}", font_size=dp(22), bold=True,
                        size_hint_y=None, height=dp(45))
            box.add_widget(top)

        amount = TextInput(
            hint_text="Monto, ejemplo 2.00",
            input_filter="float",
            multiline=False,
            font_size=dp(22),
            size_hint_y=None,
            height=dp(58)
        )
        box.add_widget(amount)

        detail = None
        if choices:
            detail = Spinner(
                text=choices[0],
                values=choices,
                size_hint_y=None,
                height=dp(52)
            )
            box.add_widget(detail)

        buttons = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
        cancel = Button(text="CANCELAR")
        save = Button(text="GUARDAR")
        buttons.add_widget(cancel)
        buttons.add_widget(save)
        box.add_widget(buttons)

        pop = Popup(title=title, content=box, size_hint=(0.90, 0.52))
        cancel.bind(on_release=pop.dismiss)

        def save_now(*_):
            try:
                value = float(amount.text.replace(",", "."))
                if value <= 0:
                    raise ValueError
            except Exception:
                amount.text = ""
                amount.hint_text = "Escribe un monto válido"
                return

            selected = detail.text if detail else ""
            self.save_movement(kind, value, selected)
            pop.dismiss()

        save.bind(on_release=save_now)
        pop.open()

    def add_trip(self, *_):
        n = self.next_trip_number()
        self.money_popup(f"Nuevo viaje {n}", "viaje", trip_number=n)

    def add_gas(self, *_):
        self.money_popup("Gasolina", "gasolina")

    def add_other(self, *_):
        self.money_popup(
            "Otro gasto", "otro",
            choices=("Lavado", "Reparación", "Aceite", "Comida", "Peaje", "Otro")
        )

    def day_rows(self, d):
        con = sqlite3.connect(DB_PATH)
        rows = con.execute("""
            SELECT id, kind, amount, detail, created_at
            FROM movements
            WHERE date(created_at)=?
            ORDER BY id
        """, (d,)).fetchall()
        con.close()
        return rows

    def totals(self, rows):
        trips = sum(a for _, k, a, _, _ in rows if k == "viaje")
        gas = sum(a for _, k, a, _, _ in rows if k == "gasolina")
        other = sum(a for _, k, a, _, _ in rows if k == "otro")
        count = sum(1 for _, k, _, _, _ in rows if k == "viaje")
        return count, trips, gas, other, trips - gas - other

    def update_screen(self):
        d = date.today().isoformat()
        rows = self.day_rows(d)
        count, trips, gas, other, net = self.totals(rows)
        self.clock.text = datetime.now().strftime("%d/%m/%Y  %I:%M %p")
        sign = "-" if net < 0 else ""
        self.summary.text = (
            "RESUMEN DE HOY\n\n"
            f"Viajes: {count}\n"
            f"Total cobrado: ${trips:.2f}\n"
            f"Gasolina: ${gas:.2f}\n"
            f"Otros gastos: ${other:.2f}\n"
            f"NETO: {sign}${abs(net):.2f}"
        )

    def choose_date(self, initial, callback):
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        inp = TextInput(text=initial, multiline=False,
                        size_hint_y=None, height=dp(50))
        ok = Button(text="USAR FECHA", size_hint_y=None, height=dp(50))
        cancel = Button(text="CANCELAR", size_hint_y=None, height=dp(45))
        box.add_widget(Label(text="Fecha: AAAA-MM-DD"))
        box.add_widget(inp)
        box.add_widget(ok)
        box.add_widget(cancel)
        pop = Popup(title="Seleccionar fecha", content=box, size_hint=(0.88, 0.45))

        def use(*_):
            try:
                datetime.strptime(inp.text.strip(), "%Y-%m-%d")
            except Exception:
                inp.text = ""
                inp.hint_text = "Fecha inválida"
                return
            callback(inp.text.strip())
            pop.dismiss()

        ok.bind(on_release=use)
        cancel.bind(on_release=pop.dismiss)
        pop.open()

    def show_history(self, *_):
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(7))
        date_in = TextInput(text=date.today().isoformat(), readonly=True,
                            multiline=False, size_hint_y=None, height=dp(45))
        pick = Button(text="ELEGIR FECHA", size_hint_y=None, height=dp(45))
        body = BoxLayout(orientation="vertical", spacing=dp(5))
        buttons = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(7))
        show = Button(text="MOSTRAR")
        close = Button(text="CERRAR")
        buttons.add_widget(show)
        buttons.add_widget(close)

        box.add_widget(date_in)
        box.add_widget(pick)
        box.add_widget(buttons)
        box.add_widget(body)

        pop = Popup(title="Historial", content=box, size_hint=(0.96, 0.88))

        def load(*_):
            body.clear_widgets()
            try:
                d = date_in.text.strip()
                datetime.strptime(d, "%Y-%m-%d")
            except Exception:
                body.add_widget(Label(text="Fecha inválida"))
                return

            rows = self.day_rows(d)
            if not rows:
                body.add_widget(Label(text="No hay movimientos en este día."))
                return

            list_box = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
            list_box.bind(minimum_height=list_box.setter("height"))
            trip_no = 0

            for rid, kind, amount, detail, ts in rows:
                tm = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").strftime("%I:%M %p")
                if kind == "viaje":
                    trip_no += 1
                    label = f"Viaje {trip_no}    {tm}    ${amount:.2f}"
                elif kind == "gasolina":
                    label = f"Gasolina    {tm}    ${amount:.2f}"
                else:
                    label = f"{detail or 'Otro'}    {tm}    ${amount:.2f}"

                row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(4))
                row.add_widget(Label(text=label, halign="left"))
                edit = Button(text="Editar", size_hint_x=None, width=dp(68))
                delete = Button(text="Borrar", size_hint_x=None, width=dp(68))
                row.add_widget(edit)
                row.add_widget(delete)
                list_box.add_widget(row)

                edit.bind(on_release=lambda _, rid=rid, k=kind, a=amount, de=detail:
                          self.edit_movement(rid, k, a, de, load))
                delete.bind(on_release=lambda _, rid=rid: self.delete_movement(rid, load))

            body.add_widget(list_box)
            c, t, g, o, n = self.totals(rows)
            body.add_widget(Label(
                text=f"Viajes: {c} | Cobrado: ${t:.2f} | Gastos: ${(g+o):.2f} | Neto: ${n:.2f}",
                bold=True, size_hint_y=None, height=dp(42)
            ))

        pick.bind(on_release=lambda *_: self.choose_date(
            date_in.text, lambda value: setattr(date_in, "text", value)))
        show.bind(on_release=load)
        close.bind(on_release=pop.dismiss)
        pop.open()
        load()

    def edit_movement(self, rid, kind, amount, detail, refresh):
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        amt = TextInput(text=f"{amount:.2f}", input_filter="float",
                        multiline=False, size_hint_y=None, height=dp(50))
        desc = TextInput(text=detail or "", hint_text="Descripción",
                         multiline=False, size_hint_y=None, height=dp(50))
        box.add_widget(amt)
        box.add_widget(desc)

        buttons = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(7))
        cancel = Button(text="Cancelar")
        save = Button(text="Guardar")
        buttons.add_widget(cancel)
        buttons.add_widget(save)
        box.add_widget(buttons)

        pop = Popup(title="Editar movimiento", content=box, size_hint=(0.90, 0.48))
        cancel.bind(on_release=pop.dismiss)

        def go(*_):
            try:
                value = float(amt.text.replace(",", "."))
                if value <= 0:
                    raise ValueError
            except Exception:
                return
            con = sqlite3.connect(DB_PATH)
            con.execute("UPDATE movements SET amount=?, detail=? WHERE id=?",
                        (value, desc.text.strip(), rid))
            con.commit()
            con.close()
            pop.dismiss()
            self.update_screen()
            refresh()

        save.bind(on_release=go)
        pop.open()

    def delete_movement(self, rid, refresh):
        con = sqlite3.connect(DB_PATH)
        con.execute("DELETE FROM movements WHERE id=?", (rid,))
        con.commit()
        con.close()
        self.update_screen()
        refresh()

    def preset_dates(self, mode):
        today = date.today()
        if mode == "hoy":
            return today, today
        if mode == "ayer":
            d = today - timedelta(days=1)
            return d, d
        if mode == "semana":
            return today - timedelta(days=today.weekday()), today
        if mode == "semana_pasada":
            monday = today - timedelta(days=today.weekday() + 7)
            return monday, monday + timedelta(days=6)
        if mode == "mes":
            return today.replace(day=1), today
        return today, today

    def show_reports(self, *_):
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(7))
        preset = Spinner(text="Hoy",
                         values=("Hoy", "Ayer", "Esta semana", "Semana pasada", "Este mes", "Personalizado"),
                         size_hint_y=None, height=dp(48))
        start = TextInput(text=date.today().isoformat(), readonly=True,
                          size_hint_y=None, height=dp(43))
        end = TextInput(text=date.today().isoformat(), readonly=True,
                        size_hint_y=None, height=dp(43))
        pick_start = Button(text="Elegir inicio", size_hint_y=None, height=dp(43))
        pick_end = Button(text="Elegir final", size_hint_y=None, height=dp(43))
        info = Label(text="Elige un período y genera el PDF.", halign="center")
        gen = Button(text="GENERAR PDF", size_hint_y=None, height=dp(54))
        share = Button(text="COMPARTIR PDF", size_hint_y=None, height=dp(50), disabled=True)
        backup = Button(text="HACER COPIA", size_hint_y=None, height=dp(48))
        close = Button(text="CERRAR", size_hint_y=None, height=dp(45))

        for w in (preset, start, pick_start, end, pick_end, info, gen, share, backup, close):
            box.add_widget(w)

        pop = Popup(title="Reportes", content=box, size_hint=(0.94, 0.92))
        share.path = None

        def apply_preset(*_):
            mode = preset.text
            mapping = {
                "Hoy": "hoy", "Ayer": "ayer", "Esta semana": "semana",
                "Semana pasada": "semana_pasada", "Este mes": "mes"
            }
            if mode in mapping:
                d1, d2 = self.preset_dates(mapping[mode])
                start.text = d1.isoformat()
                end.text = d2.isoformat()

        def generate(*_):
            try:
                d1 = datetime.strptime(start.text.strip(), "%Y-%m-%d").date()
                d2 = datetime.strptime(end.text.strip(), "%Y-%m-%d").date()
                if d2 < d1:
                    raise ValueError
            except Exception:
                info.text = "Revisa las fechas."
                return

            if not REPORTLAB_OK:
                info.text = "Falta ReportLab. Instálalo en Pydroid."
                return

            path = self.make_pdf(d1, d2)
            share.path = path
            share.disabled = False
            info.text = "PDF creado correctamente."

        preset.bind(on_release=apply_preset)
        pick_start.bind(on_release=lambda *_: self.choose_date(
            start.text, lambda value: setattr(start, "text", value)))
        pick_end.bind(on_release=lambda *_: self.choose_date(
            end.text, lambda value: setattr(end, "text", value)))
        gen.bind(on_release=generate)
        share.bind(on_release=lambda *_: self.share_pdf(share.path))
        backup.bind(on_release=lambda *_: self.show_backup())
        close.bind(on_release=pop.dismiss)

        pop.open()

    def make_pdf(self, d1, d2):
        # Crear primero el PDF dentro de la app.
        out = Path(self.user_data_dir) / f"reporte_{d1}_{d2}.pdf"
        c = canvas.Canvas(str(out), pagesize=letter)
        W, H = letter
        y = H - 45

        c.setFont("Helvetica-Bold", 17)
        c.drawString(45, y, "REPORTE DE TRABAJO")
        y -= 22
        c.setFont("Helvetica", 10)
        c.drawString(45, y, f"Periodo: {d1.strftime('%d/%m/%Y')} al {d2.strftime('%d/%m/%Y')}")
        y -= 28

        grand = [0, 0, 0, 0, 0]
        cur = d1

        while cur <= d2:
            rows = self.day_rows(cur.isoformat())
            if rows:
                if y < 80:
                    c.showPage()
                    y = H - 45
                c.setFont("Helvetica-Bold", 12)
                c.drawString(45, y, cur.strftime("%A %d/%m/%Y"))
                y -= 17

                c.setFont("Helvetica", 9)
                trip_no = 0
                for _, kind, amount, detail, ts in rows:
                    tm = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
                    if kind == "viaje":
                        trip_no += 1
                        label = f"Viaje {trip_no}"
                    elif kind == "gasolina":
                        label = "Gasolina"
                    else:
                        label = f"Otro: {detail or 'Otro'}"
                    c.drawString(55, y, f"{tm}   {label}")
                    c.drawRightString(W - 55, y, f"${amount:.2f}")
                    y -= 13
                    if y < 55:
                        c.showPage()
                        y = H - 45

                vals = self.totals(rows)
                for i in range(5):
                    grand[i] += vals[i]

                y -= 3
                c.setFont("Helvetica-Bold", 9)
                c.drawString(55, y, f"Viajes {vals[0]} | Cobrado ${vals[1]:.2f} | "
                                    f"Gas ${vals[2]:.2f} | Otros ${vals[3]:.2f} | Neto ${vals[4]:.2f}")
                y -= 22
            cur += timedelta(days=1)

        if y < 80:
            c.showPage()
            y = H - 45

        c.setFont("Helvetica-Bold", 13)
        c.drawString(45, y, "TOTAL DEL PERIODO")
        y -= 20
        c.setFont("Helvetica", 10)
        c.drawString(55, y,
                      f"Viajes: {grand[0]}   Cobrado: ${grand[1]:.2f}   "
                      f"Gasolina: ${grand[2]:.2f}   Otros: ${grand[3]:.2f}   Neto: ${grand[4]:.2f}")
        c.save()

        if ANDROID_OK:
            try:
                self.publish_pdf_to_downloads(str(out))
            except Exception:
                pass

        return str(out)

    def publish_pdf_to_downloads(self, path):
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        ContentValues = autoclass("android.content.ContentValues")
        MediaStore = autoclass("android.provider.MediaStore")
        MediaColumns = autoclass("android.provider.MediaStore$MediaColumns")
        Downloads = autoclass("android.provider.MediaStore$Downloads")
        Environment = autoclass("android.os.Environment")

        activity = PythonActivity.mActivity
        resolver = activity.getContentResolver()

        values = ContentValues()
        values.put(MediaColumns.DISPLAY_NAME, Path(path).name)
        values.put(MediaColumns.MIME_TYPE, "application/pdf")
        values.put(
            MediaColumns.RELATIVE_PATH,
            Environment.DIRECTORY_DOWNLOADS + "/Mi Trabajo"
        )
        values.put(MediaColumns.IS_PENDING, 1)

        uri = resolver.insert(Downloads.EXTERNAL_CONTENT_URI, values)

        if uri is None:
            raise RuntimeError("Android no pudo crear el archivo en Descargas.")

        try:
            output = resolver.openOutputStream(uri)
            if output is None:
                raise RuntimeError("No se pudo abrir el archivo de destino.")

            try:
                with open(path, "rb") as source:
                    while True:
                        chunk = source.read(64 * 1024)
                        if not chunk:
                            break
                        output.write(bytearray(chunk))
            finally:
                output.close()

            done = ContentValues()
            done.put(MediaColumns.IS_PENDING, 0)
            resolver.update(uri, done, None, None)
            return uri

        except Exception:
            try:
                resolver.delete(uri, None, None)
            except Exception:
                pass
            raise

    def share_pdf(self, path):
        if not path:
            return

        if ANDROID_OK:
            try:
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                Intent = autoclass("android.content.Intent")
                MediaColumns = autoclass("android.provider.MediaStore$MediaColumns")
                Downloads = autoclass("android.provider.MediaStore$Downloads")
                Environment = autoclass("android.os.Environment")

                activity = PythonActivity.mActivity
                resolver = activity.getContentResolver()

                file_name = Path(path).name

                projection = [
                    MediaColumns._ID,
                    MediaColumns.DISPLAY_NAME
                ]
                selection = (
                    MediaColumns.DISPLAY_NAME + "=? AND " +
                    MediaColumns.RELATIVE_PATH + "=?"
                )
                selection_args = [
                    file_name,
                    Environment.DIRECTORY_DOWNLOADS + "/Mi Trabajo/"
                ]

                cursor = resolver.query(
                    Downloads.EXTERNAL_CONTENT_URI,
                    projection,
                    selection,
                    selection_args,
                    None
                )

                uri = None
                if cursor is not None:
                    try:
                        if cursor.moveToFirst():
                            id_index = cursor.getColumnIndex(MediaColumns._ID)
                            media_id = cursor.getLong(id_index)
                            uri = Downloads.getContentUri("external", media_id)
                    finally:
                        cursor.close()

                if uri is None:
                    uri = self.publish_pdf_to_downloads(path)

                intent = Intent(Intent.ACTION_SEND)
                intent.setType("application/pdf")
                intent.putExtra(Intent.EXTRA_STREAM, uri)
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)

                chooser = Intent.createChooser(intent, "Compartir reporte")
                chooser.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                activity.startActivity(chooser)
                return

            except Exception as exc:
                self.message(
                    "No se pudo compartir",
                    "El PDF sí fue generado.\n\n"
                    "Puedes encontrarlo en:\n"
                    "Descargas/Mi Trabajo\n\n"
                    f"Detalle: {exc}"
                )
                return

        self.message("PDF listo", f"El PDF se guardó en:\n{path}")

    def backup_database(self):
        folder = Path(self.user_data_dir) / "backups"
        folder.mkdir(parents=True, exist_ok=True)
        name = f"mi_trabajo_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        dest = folder / name
        shutil.copy2(DB_PATH, dest)
        return str(dest)

    def show_backup(self, *_):
        path = self.backup_database()
        self.message("Copia de seguridad", f"Copia creada correctamente.\n\n{path}")

    def message(self, title, text):
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        box.add_widget(Label(text=text, halign="center"))
        close = Button(text="CERRAR", size_hint_y=None, height=dp(48))
        box.add_widget(close)
        pop = Popup(title=title, content=box, size_hint=(0.90, 0.45))
        close.bind(on_release=pop.dismiss)
        pop.open()


if __name__ == "__main__":
    MiTrabajoApp().run()
