import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import os
from pypdf import PdfReader, PdfWriter
import concurrent.futures
import logging
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"


def is_scanned_pdf(file_path):
    """Check if a PDF is a scanned PDF by trying to extract text."""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            for page in pdf_reader.pages:
                if page.extract_text():
                    return False
            return True
    except Exception as e:
        LOGGER.warning(f"Failed to process PDF: {os.path.basename(file_path)} - {e}")
        return False

def process_page(page_num, pdf_document, dpi):
    try:
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72))
        img = Image.open(io.BytesIO(pix.tobytes()))
        ocr_pdf = pytesseract.image_to_pdf_or_hocr(img, extension='pdf', config='--psm 3')
        ocr_pdf_reader = PdfReader(io.BytesIO(ocr_pdf))
        ocr_pdf_page = ocr_pdf_reader.pages[0]
        return page_num, ocr_pdf_page
    except Exception as e:
        print(f"Error processing page {page_num}: {e}")
        return page_num, None

def convert_scanned_pdf_to_ocr(pdf_path,*args,dpi=111):
    if args:
        output_path=args[0]
    else:
        output_path=pdf_path
    pdf_document = fitz.open(pdf_path)
    pdf_writer = PdfWriter()

    # Use a list to store processed pages
    pages = [None] * pdf_document.page_count

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(process_page, page_num, pdf_document, dpi): page_num for page_num in range(pdf_document.page_count)}
        for future in concurrent.futures.as_completed(futures):
            page_num, ocr_pdf_page = future.result()
            if ocr_pdf_page:
                # Store the page in the correct position
                pages[page_num] = ocr_pdf_page

    # Add pages in the correct order with the correct size
    for page_num, page in enumerate(pages):
        if page:
            original_page = pdf_document.load_page(page_num)
            page.scale_to(original_page.rect.width, original_page.rect.height)
            pdf_writer.add_page(page)
   
    with open(output_path, 'wb') as f_out:
        pdf_writer.write(f_out)
