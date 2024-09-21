import cv2
import pytesseract

# Path to the input image and the output image
image_path = 'color_correction_output/test.png'
output_image_path = 'section_output/output_with_text.png'
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Load the image
img = cv2.imread(image_path)

# Convert the image to grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Perform OCR and get bounding boxes of the detected text
h, w, _ = img.shape
boxes = pytesseract.image_to_boxes(gray)

# Loop over each detected text box and draw the character at its location
for box in boxes.splitlines():
    # print(box.split(' '))
    b = box.split(' ')
    char = b[0]  # Detected character
    x_start, y_start = int(b[1]), int(b[2])
    x_end, y_end = int(b[3]), int(b[4])
    if (y_start < 160 or True):
        # OpenCV uses (x, y) coordinates with the origin at the top-left,
        # so we need to invert the y-coordinates from Tesseract
        # Draw a rectangle around the detected character (optional)
        cv2.rectangle(img, (x_start, h - y_start), (x_end, h - y_end), (0, 255, 0), 2)

        # Write the character at the top-left corner of the bounding box
        # Adjust the y-coordinate to slightly offset the text vertically within the box
        font_scale = 1  # You can adjust the scale if needed
        font_thickness = 2
        cv2.putText(img, char, (x_start, h - y_start), cv2.FONT_HERSHEY_SIMPLEX, 
                    font_scale, (255, 0, 0), font_thickness)

# Save the image with bounding boxes and text
cv2.imwrite(output_image_path, img)

# Optionally, display the image (you can comment this out if running in a headless environment)
cv2.imshow('Detected Text', img)
cv2.waitKey(0)
cv2.destroyAllWindows()

print(f"Image with characters written saved to: {output_image_path}")
