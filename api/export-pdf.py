import io
import json
from http.server import BaseHTTPRequestHandler
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        size = int(self.headers.get("Content-Length", 0))
        text = str(json.loads(self.rfile.read(size) or b"{}").get("text", "Document Denta Atelier"))
        stream = io.BytesIO()
        pdf = canvas.Canvas(stream, pagesize=A4)
        pdf.setTitle("Denta Atelier")
        pdf.setFont("Helvetica-Bold", 17)
        pdf.drawString(48, 800, "Denta Atelier")
        pdf.setFont("Helvetica", 10)
        y = 770
        for line in text.splitlines() or [""]:
            pdf.drawString(48, y, line.encode("ascii", "replace").decode("ascii")[:95])
            y -= 15
            if y < 55:
                pdf.showPage(); y = 800; pdf.setFont("Helvetica", 10)
        pdf.save()
        content = stream.getvalue()
        self.send_response(200)
        self.send_header("Content-Type", "application/pdf")
        self.send_header("Content-Disposition", 'attachment; filename="denta-atelier-document.pdf"')
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)
