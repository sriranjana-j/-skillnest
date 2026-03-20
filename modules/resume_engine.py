from xhtml2pdf import pisa
from django.template.loader import render_to_string
from django.conf import settings
import uuid, os

def generate_pdf_resume(data, photo, template):
    html = render_to_string(
        f"resume_templates/{template}.html",
        {"data": data, "photo": photo, "pdf": True},
    )

    output_name = os.path.join(settings.BASE_DIR, "static", f"{uuid.uuid4()}.pdf")
    with open(output_name, "wb") as pdf:
        pisa.CreatePDF(html, dest=pdf)
    return output_name
