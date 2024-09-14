import cv2
import pytesseract

# Path to the input image
image_path = 'color_correction_output/test.png'
output_image_path = 'section_output/output_with_text.png'
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Load the image
img = cv2.imread(image_path)

# Check if the image was loaded successfully
if img is None:
    print(f"Error: Unable to load the image from {image_path}.")
else:
    print("Image loaded successfully.")

    # Convert the image to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Perform OCR and get bounding boxes of the detected text
    h, w, _ = img.shape
    boxes = pytesseract.image_to_boxes(gray)

    # Define the threshold for the left side of the image
    left_side_threshold = int(w * 0.25)  # 25% from the left edge of the image

    # Initialize a list to store bounding boxes of question numbers
    question_numbers = []

    # Loop over the detected text boxes and filter by position and content (numbers)
    for box in boxes.splitlines():
        b = box.split(' ')
        char = b[0]  # Detected character
        x_start, y_start = int(b[1]), int(b[2])
        x_end, y_end = int(b[3]), int(b[4])

        # Check if the character is on the left side of the image
        if x_start < left_side_threshold:
            # Check if the character is a digit (question number) or part of it
            if char.isdigit():
                # Add the bounding box and character to the list of question numbers
                question_numbers.append({'char': char, 'start': [x_start, y_start], 'end': [x_end, y_end]})

                # Draw a rectangle around the question number (optional visualization)
                cv2.rectangle(img, (x_start, h - y_start), (x_end, h - y_end), (0, 255, 0), 2)
                # Optionally, write the number on the image
                cv2.putText(img, char, (x_start, h - y_start), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    # Save the output image with detected question numbers
    cv2.imwrite(output_image_path, img)

    print(f"Question numbers detected: {question_numbers}")
    print(f"Image with question numbers highlighted saved to: {output_image_path}")

    # Optionally, display the image (you can comment this out if running in a headless environment)
    cv2.imshow('Detected Question Numbers', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
