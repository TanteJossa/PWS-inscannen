import fitz
import math


pdffile = "input.pdf"
doc = fitz.open(pdffile)
for i in range(doc.page_count):
    page = doc.load_page(i)  # number of page
    pix = page.get_pixmap()
    output = f"image_output/outfile_i{i}_student{math.floor(i/2)}_{i % 2}.png"
    pix.save(output)

doc.close()