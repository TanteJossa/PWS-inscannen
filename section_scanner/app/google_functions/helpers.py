import base64
import uuid
import json 
from PIL import Image, ImageDraw, ImageFont
import os 
import numpy as np
from io import BytesIO
import cv2

def png_to_base64(file_path, quality=1):
    if not file_path.endswith('.png'):
        raise ValueError("Input file must be a PNG image.")
    if quality != 1:
        # https://platform.openai.com/docs/guides/vision 

        pillow_image = Image.open(file_path)
        
        new_width = int(pillow_image.width * quality)
        new_height = int(float(pillow_image.size[1]) * quality)
        
        resized_image = pillow_image.resize((new_width, new_height))
        buffered = BytesIO()
        resized_image.save(buffered, format="PNG")
        base64_string = base64.b64encode(buffered.getvalue()).decode('utf-8')
    else:
        with open(file_path, "rb") as image_file:
            base64_string = base64.b64encode(image_file.read()).decode("utf-8")
    return "data:image/png;base64,"+base64_string

def base64_to_png(base64_string, output_path):
    if not output_path.endswith('.png'):
        raise ValueError("Output file must have a .png extension.")
    image_data = base64.b64decode(base64_string.replace('data:image/png;base64,', ''))
    with open(output_path, "wb") as output_file:
        output_file.write(image_data)

def get_random_id():
    return str(uuid.uuid4())



def clamp(n, min, max): 
    if n < min: 
        return min
    elif n > max: 
        return max
    else: 
        return n 



# Example usage with the provided squares and a new output path

def get_black_square_data(image,  min_size=15):
    # Convert the image to grayscale to help detect the black squares
    gray_img = image.convert('L')
    gray_img.point(lambda x: 0 if x < 128 else 255, '1')
    
    # Convert the PIL image to a NumPy array
    arr_image = np.array(gray_img.copy())

    # Threshold the array to ensure it's binary
    binary_image = (arr_image < 128).astype(int)  # Assuming black is below 128
    
    # Ensure the binary image is in the correct format
    if binary_image.dtype != np.uint8:
        binary_image = binary_image.astype(np.uint8)

    # Find contours in the binary image
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour_image =  image.copy()

    # List to store rectangle properties
    rectangles = []

    # Iterate over contours
    for contour in contours:
        # Get the bounding box for each contour
        x, y, w, h = cv2.boundingRect(contour)
        
        # oly select filled boxes on the right
        if (x > int(2/21 * image.width)):
            continue
        
        # only if black squares
        average_color = np.mean(arr_image[ y:y+h, x:x+w])

        if (average_color > 120):
            continue
        
        
        # Check if the bounding box is a square and larger than 15x15
        if w >= min_size and h >= min_size and abs(w - h) <= 2:  # Allow a small tolerance for non-perfect squares
            # Append the rectangle properties: (start_height, height, x_min, x_max)
            rectangles.append((y, h, x, x + w))
            
            draw = ImageDraw.Draw(contour_image)
            contour_points = [(int(point[0][0]), int(point[0][1])) for point in contour]
            draw.polygon(contour_points, outline=(0, 255, 0), width=2)
            # contour_image = draw.polygon(contour, fill=(0,255,0))

    
    
    return rectangles, gray_img, contour_image


def stack_images_vertically(img1, img2):

    # Get the dimensions of both images
    width1, height1 = img1.size
    width2, height2 = img2.size

    # Calculate the dimensions for the new image
    new_width = max(width1, width2)
    new_height = height1 + height2

    # Create a new blank image with the calculated dimensions
    new_image = Image.new('RGB', (new_width, new_height))

    # Paste the first image at the top
    new_image.paste(img1, (0, 0))

    # Paste the second image below the first image
    new_image.paste(img2, (0, height1))
    
    return new_image

