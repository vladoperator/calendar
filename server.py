"""Local server for Denta Atelier demo exports."""
import io
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


class Handler(SimpleHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")
        if self.path == "/export-visits":
            stream = io.BytesIO()
            book = Workbook()
            sheet = book.active
            sheet.title = "Jurnal vizite"
            sheet.append(["Pacient", "Telefon", "Data", "Servicii"])
            for cell in sheet[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="1B1C20")
            for row in payload.get("rows", []):
                sheet.append(row)
            for column, width in {"A": 28, "B": 18, "C": 16, "D": 25}.items():
                sheet.column_dimensions[column].width = width
            book.save(stream)
            self.send_file(stream.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "jurnal-vizite.xlsx")
            return
        if self.path == "/export-pdf":
            stream = io.BytesIO()
            pdf = canvas.Canvas(stream, pagesize=A4)
            pdf.setTitle("Denta Atelier")
            y = 800
            pdf.setFont("Helvetica-Bold", 17)
            pdf.drawString(48, y, "Denta Atelier")
            y -= 34
            pdf.setFont("Helvetica", 10)
            for raw in str(payload.get("text", "Document Denta Atelier")).splitlines() or [""]:
                line = raw.encode("ascii", "replace").decode("ascii")
                while stringWidth(line, "Helvetica", 10) > 510:
                    cut = max(line.rfind(" ", 0, 90), 1)
                    pdf.drawString(48, y, line[:cut])
                    y -= 15
                    line = line[cut:].lstrip()
                pdf.drawString(48, y, line)
                y -= 15
                if y < 55:
                    pdf.showPage(); y = 800; pdf.setFont("Helvetica", 10)
            pdf.save()
            self.send_file(stream.getvalue(), "application/pdf", "denta-atelier-document.pdf")
            return
        self.send_error(404)

    def send_file(self, content, mime, name):
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Disposition", f'attachment; filename="{name}"')
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8080), Handler).serve_forever()
