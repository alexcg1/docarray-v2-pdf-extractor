import pdfplumber


class PDFExtractor:
    def extract_text(filename):
        with pdfplumber.open(filename) as pdf:
            for page in pdf.pages:
                print(page)
