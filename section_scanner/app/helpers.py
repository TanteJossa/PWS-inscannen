import base64
import uuid
import json 
from PIL import Image, ImageDraw, ImageFont
import os 
import numpy as np
from io import BytesIO
import cv2
from pyzbar.pyzbar import decode, Decoded
import io
import segno
from collections import defaultdict
from typing import Dict, Any
import hashlib
import json

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

# https://pyimagesearch.com/2014/08/25/4-point-opencv-getperspective-transform-example/
def order_points(pts):
	# initialzie a list of coordinates that will be ordered
	# such that the first entry in the list is the top-left,
	# the second entry is the top-right, the third is the
	# bottom-right, and the fourth is the bottom-left
	rect = np.zeros((4, 2), dtype = "float32")
	# the top-left point will have the smallest sum, whereas
	# the bottom-right point will have the largest sum
	s = np.array(pts).sum(axis = 1)
	rect[0] = pts[np.argmin(s)]
	rect[2] = pts[np.argmax(s)]
	# now, compute the difference between the points, the
	# top-right point will have the smallest difference,
	# whereas the bottom-left will have the largest difference
	diff = np.diff(pts, axis = 1)
	rect[1] = pts[np.argmin(diff)]
	rect[3] = pts[np.argmax(diff)]
	# return the ordered coordinates
	return rect

def four_point_transform(image, pts):
    # obtain a consistent order of the points and unpack them
    # individually
    rect = order_points(pts)

    (tl, tr, br, bl) = rect

    # compute the width of the new image, which will be the
    # maximum distance between bottom-right and bottom-left
    # x-coordiates or the top-right and top-left x-coordinates
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    # compute the height of the new image, which will be the
    # maximum distance between the top-right and bottom-right
    # y-coordinates or the top-left and bottom-left y-coordinates
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    # now that we have the dimensions of the new image, construct
    # the set of destination points to obtain a "birds eye view",
    # (i.e. top-down view) of the image, again specifying points
    # in the top-left, top-right, bottom-right, and bottom-left
    # order
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype = "float32")

    # compute the perspective transform matrix and then apply it
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))

    # return the warped image
    return warped

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
        _, _, qr1_width, qr1_height = qr1.rect  # This is a tuple (x, y, width, height)
        _, _, qr2_width, qr2_height = qr2.rect  # This is a tuple (x, y, width, height)
        
        # Get the data from the QR code
        if (qr1.polygon[0][0] < qr2.polygon[0][0]):
            pol1 = qr1.polygon
            pol2 = qr2.polygon
        else:
            pol2 = qr1.polygon
            pol1 = qr2.polygon        
                        
        # https://docs.google.com/drawings/d/1mjl77u_CYfVI8T09_lvpzwu73qHWqMe3QVYpb99blr8
        p1, p2, p4, p3 = order_points(pol1)
        p5, p6, p8, p7 = order_points(pol2)
        
        pol_top_left = p2
        pol_bottom_right = p7
        
        a1 = (p2[1] - p1[1]) / (p2[0] - p1[0])
        if (abs(a1) > 0.02):
            b1 = p2[1] - p2[0] * a1

            a2 = (p5[1] - p7[1]) / (p5[0] - p7[0])
            b2 = p5[1] - p5[0] * a2
            
            x1 = (b2 - b1) / (a1 - a2)
            y1 = a1 * x1 + b1
            pol_top_right = (x1, y1)
            
            a3 = (p4[1] - p2[1]) / (p4[0] - p2[0])
            b3 = p4[1] - p4[0] * a3
            
            a4 = (p7[1] - p8[1]) / (p7[0] - p8[0])
            b4 = p7[1] - p7[0] * a4
            
            x2 = (b4 - b3) / (a3 - a4)
            y2 = a3 * x2 + b3
            pol_bottom_left = (x2, y2)
        
            coords = [pol_top_left, pol_top_right, pol_bottom_right, pol_bottom_left]
        else:
            coords = [pol_top_left, (p7[0],p4[1]), pol_bottom_right, (p4[0], p7[1])]

        coords = [(x[0].item(), x[1].item()) for x in coords]
        # print(coords, pillow_image.width, pillow_image.height)

        qr_code_coords.append({
            # "coords": [top_left, bottom_right],
            "polygon": coords,
            "data": qr1_data
        })
        font = ImageFont.load_default(size=pillow_image.width / 35)
        
        # Draw the rectangle (color: green, thicknessp: 3)
        draw.polygon(coords, outline="green", width=10)
        for index, coord in enumerate([p1, p2, p3, p4,  p5, p6, p7, p8]):
            draw.point(coord, 'red')
            draw.text(coord,'p'+str(index+1), fill="blue", font=font, stroke_width=3)
            
        for index, coord in enumerate(coords):
            draw.point(coord, 'red')
            draw.text(coord,'c'+str(index+1), fill="red", font=font, stroke_width=3)
            
        # Draw the rectangle (color: green, thicknessp: 3)
        draw.polygon(coords, outline="green", width=10)
        
        # Display the decoded QR code data on the image
        font = ImageFont.load_default(size=15)
        text_position = (pol_top_left[0], pol_top_left[1] - 10)  # Place text above the rectangle
        draw.text(text_position, qr1_data, fill="green", font=font)


    return qr_code_coords, pillow_image
# Example usage with the provided squares and a new output path

def get_black_square_data(image,  min_size=15):

    # Convert the image to grayscale to help detect the black squares
    gray_img = image.convert('L')
    gray_img.point(lambda x: 0 if x < 150 else 255, '1')
    # Convert the PIL image to a NumPy array
    arr_image = np.array(gray_img.copy())
    # Threshold the array to ensure it's binary
    binary_image = (arr_image < 150).astype(int)  # Assuming black is below 150

    arr_binary_image = np.array(binary_image.copy())
    
    # Ensure the binary image is in the correct format
    if binary_image.dtype != np.uint8:
        binary_image = binary_image.astype(np.uint8)

    # cv2.imwrite('./tempshow/binary.png', binary_image*255)
    
    # Find contours in the binary image
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour_image =  image.copy()
    
    temp = image.copy()
    

    # for contour in contours:
    #     draw = ImageDraw.Draw(temp)
    #     contour_points = [(int(point[0][0]), int(point[0][1])) for point in contour if len(point[0]) ==2 ]
    #     if (len(contour_points) > 1):
    #         draw.polygon(contour_points, outline=(0, 255, 0), width=2)
        
    # base64_to_png(pillow_to_base64(temp), './test_output/countour.png')

    

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
        
        # Check if the bounding box is a square and larger than 15x15
        if w >= min_size and h >= min_size:  # Allow a small tolerance for non-perfect squares
            # Append the rectangle properties: (start_height, height, x_min, x_max)
            rectangles.append((y, h, x, x + w))
            
            draw = ImageDraw.Draw(contour_image)
            contour_points = [(int(point[0][0]), int(point[0][1])) for point in contour]
            draw.polygon(contour_points, outline=(0, 255, 0), width=2)
    
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


def dict_hash(dictionary: Dict[str, Any]) -> str:
    """MD5 hash of a dictionary."""
    dhash = hashlib.md5()
    # We need to sort arguments so {'a': 1, 'b': 2} is
    # the same as {'b': 2, 'a': 1}
    encoded = json.dumps(dictionary, sort_keys=True).encode()
    dhash.update(encoded)
    return dhash.hexdigest()