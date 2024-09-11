import docx2txt
from PIL import Image
import pytesseract
from docx import Document
import os
import sys

# Path to Tesseract-OCR executable (Update if necessary)
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

def convert_scanned_word_to_searchable_word(scanned_word_path, output_word_path):
    # Extract images from the scanned Word document
    temp_dir = "temp_images"
    os.makedirs(temp_dir, exist_ok=True)
    docx2txt.process(scanned_word_path, temp_dir)

    # Create a new Word document for the searchable text
    doc = Document()

    # Iterate through extracted images and perform OCR
    for image_file in os.listdir(temp_dir):
        image_path = os.path.join(temp_dir, image_file)
        if image_file.endswith(('png', 'jpg', 'jpeg')):
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            doc.add_paragraph(text)

    # Save the searchable Word document
    doc.save(output_word_path)
    print(f"Searchable Word document saved to {output_word_path}")

    # Clean up temporary image files
    for image_file in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, image_file))
    os.rmdir(temp_dir)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python word_to_searchable.py <scanned_word_path> <output_word_path>")
    else:
        import sys
        scanned_word_path = sys.argv[1]
        output_word_path = sys.argv[2]
        convert_scanned_word_to_searchable_word(scanned_word_path, output_word_path)
