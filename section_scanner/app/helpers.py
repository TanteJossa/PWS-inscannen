import base64
import uuid
import json 
from PIL import Image, ImageDraw, ImageFont
import os 
import numpy as np
from io import BytesIO
import cv2
from pyzbar.pyzbar import decode
import io
import segno
from collections import defaultdict

ppi = 200
inch_per_cm = 0.393701

cm_to_px = lambda x: int(x*ppi*inch_per_cm)

def pillow_to_base64(pillow_image):
    buffered = BytesIO()
    pillow_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    
    if not img_str.startswith('data:image'):
        img_str = "data:image/png;base64," + img_str
    
    return img_str

def base64_to_pillow(base64_string):
    # Remove the data URL prefix if present
    if base64_string.startswith('data:image'):
        base64_string = base64_string.split(',')[1]
            

    padding_needed = len(base64_string) % 4
    if padding_needed:
        base64_string += '=' * (4 - padding_needed)
    
    # Step 1: Decode the base64 string into bytes
    image_data = base64.b64decode(base64_string)
        
    # Step 2: Use a BytesIO object to make the byte data readable by PIL
    image_bytes = io.BytesIO(image_data)

    # Step 3: Open the image using PIL
    image = Image.open(image_bytes)

    return image

def cv2_to_base64(cv2_image):
    
    success, buffer = cv2.imencode('.png', cv2_image)

    if success:
        # Step 3: Convert the buffer to a base64 string
        base64_string = base64.b64encode(buffer).decode('utf-8')
        
        if not base64_string.startswith('data:image'):
            base64_string = "data:image/png;base64," + base64_string
        
        return base64_string
    else:
        return None
    
def base64_to_cv2(base64_string):
    
    # Remove the data URL prefix if present
    if base64_string.startswith('data:image'):
        base64_string = base64_string.split(',')[1]
        
    padding_needed = len(base64_string) % 4
    if padding_needed:
        base64_string += '=' * (4 - padding_needed)
    
    # Step 1: Decode the base64 string to bytes
    image_data = base64.b64decode(base64_string)
    
    # Step 2: Convert the bytes to a NumPy array
    np_array = np.frombuffer(image_data, np.uint8)
    
    # Step 3: Decode the NumPy array to an image using OpenCV
    image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    
    return image

def pillow_to_cv2(pillow_image):
    return cv2.cvtColor(np.array(pillow_image), cv2.COLOR_RGB2BGR)

def cv2_to_pillow(cv2_image):
    return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB))


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
    if not base64_string.startswith('data:image'):
        base64_string = "data:image/png;base64," + base64_string
    
    return base64_string #

def base64_to_png(base64_string, output_path):
    if not output_path.endswith('.png'):
        raise ValueError("Output file must have a .png extension.")
    image_data = base64.b64decode(base64_string.replace("data:image/png;base64,",""))
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


def scan_qrcode_from_image(pillow_image):    

    # Ensure the image is in RGB mode (in case it's RGBA or grayscale)
    if pillow_image.mode != 'RGB':
        pillow_image = pillow_image.convert('RGB')
    
    # Convert Pillow image to OpenCV format (numpy array)
    open_cv_image = np.array(pillow_image)

    # Convert RGB to BGR (OpenCV uses BGR format)
    open_cv_image = open_cv_image[:, :, ::-1]

    # Decode QR codes
    qr_codes = decode(open_cv_image)

    # Create a drawing context
    draw = ImageDraw.Draw(pillow_image)

    qr_code_coords = []

    # Iterate through detected QR codes
    for qr1, qr2 in pair_same_output(qr_codes, lambda x: x.data):
                
        # Get the data from the QR code
        qr1_data = qr1.data.decode('utf-8')
        qr2_data = qr2.data.decode('utf-8')

        # Get the bounding box (rectangle)
        rect1_points = qr1.rect  # This is a tuple (x, y, width, height)
        rect2_points = qr2.rect  # This is a tuple (x, y, width, height)

        p1 = (rect1_points[0] , rect1_points[1] + rect2_points[3])
        p2 = (rect2_points[0]+ rect1_points[2], rect2_points[1])

        if (rect1_points[0] < rect2_points[0]):
            top_left = p1
            bottom_right = p2
        else:
            top_left = p2
            bottom_right = p1
        

        qr_code_coords.append({
            "coords": [top_left, bottom_right],
            "data": qr1_data
        })
        
        # Draw the rectangle (color: green, thicknessp: 3)
        draw.rectangle([top_left, bottom_right], outline="green", width=10)
        
        # Display the decoded QR code data on the image
        font = ImageFont.load_default(size=15)
        text_position = (top_left[0], top_left[1] - 10)  # Place text above the rectangle
        draw.text(text_position, qr1_data, fill="green", font=font)


    return qr_code_coords, pillow_image
# Example usage with the provided squares and a new output path

def get_black_square_data(image,  min_size=15):

    # Convert the image to grayscale to help detect the black squares
    gray_img = image.convert('L')
    gray_img.point(lambda x: 0 if x < 128 else 255, '1')
    
    # Convert the PIL image to a NumPy array
    arr_image = np.array(gray_img.copy())

    # Threshold the array to ensure it's binary
    binary_image = (arr_image < 150).astype(int)  # Assuming black is below 128

    arr_binary_image = np.array(binary_image.copy())
    
    # Ensure the binary image is in the correct format
    if binary_image.dtype != np.uint8:
        binary_image = binary_image.astype(np.uint8)

    # cv2.imwrite('./tempshow/binary.png', binary_image*255)
    
    # Find contours in the binary image
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour_image =  image.copy()
    
    # temp = image.copy()
    

    # for contour in contours:
    #     draw = ImageDraw.Draw(temp)
    #     contour_points = [(int(point[0][0]), int(point[0][1])) for point in contour]
    #     draw.polygon(contour_points, outline=(0, 255, 0), width=2)

    

    # List to store rectangle properties
    rectangles = []

    # Iterate over contours
    for contour in contours:
        # Get the bounding box for each contour
        x, y, w, h = cv2.boundingRect(contour)
        
        # oly select filled boxes on the right
        if (x > int(1.9/21 * image.width)):
            continue
        

        # only if black squares
        average_color = np.mean(arr_binary_image[ y:y+h, x:x+w])
        
        if (average_color < 0.7):
            continue
        
        # draw_temp = ImageDraw.Draw(contour_image)
        # contour_points = [(int(point[0][0]), int(point[0][1])) for point in contour]
        

        
        # Check if the bounding box is a square and larger than 15x15
        if w >= min_size and h >= min_size:  # Allow a small tolerance for non-perfect squares
            # Append the rectangle properties: (start_height, height, x_min, x_max)
            rectangles.append((y, h, x, x + w))
            
            draw = ImageDraw.Draw(contour_image)
            contour_points = [(int(point[0][0]), int(point[0][1])) for point in contour]
            draw.polygon(contour_points, outline=(0, 255, 0), width=2)
            
            # id = get_random_id()
            # cv2.imwrite('./tempshow/'+str(int(average_color*100))+'.png', arr_binary_image[ y:y+h, x:x+w] * 255)

            # draw_temp.polygon(contour_points, outline=(0, 255, 0), width=2)

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

def create_qr(data, height=1):
    qrcode = segno.make(data, boost_error=False, micro=False)
    out = io.BytesIO()
    qrcode.save(out, scale=height, border=0, kind='png')
    out.seek(0)
    local_img = Image.open(out)

    return local_img

def consecutive_pairs(lst):
    # Create pairs by zipping the list with itself offset by one element
    return [(lst[i], lst[i + 1]) for i in range(0, len(lst) - 1, 2)]

def pair_same_output(lst, func):
    # Create a dictionary to group elements by their transformed values
    grouped = defaultdict(list)
    for item in lst:
        key = func(item)
        grouped[key].append(item)

    # Generate pairs from the grouped values
    pairs = []
    for items in grouped.values():
        # Add pairs only if there are at least two items with the same output
        pairs.extend((items[i], items[i + 1]) for i in range(0, len(items) - 1, 2))
    
    return pairs

