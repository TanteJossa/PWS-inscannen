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
import re 

ppi = 200
inch_per_cm = 0.393701

cm_to_px = lambda x: int(x*ppi*inch_per_cm)


is_localhost = False

GPT_URL = 'https://gpt-function-771520566941.europe-west4.run.app/gpt'
DOC_URL = 'https://docgen-function-771520566941.europe-west4.run.app'

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

def json_from_string(s:str):
    # Find the first '{' and last '}' in the string
    first_brace = s.find('{')
    last_brace = s.rfind('}')
    
    # Check if braces exist and are correctly ordered
    if first_brace == -1 or last_brace == -1 or first_brace >= last_brace:
        return None
    
    # Extract the substring between the first '{' and last '}'
    json_str = s[first_brace : last_brace + 1]

    try:
        # Parse the JSON string
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None


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

def findSquares(binary_img):
    """
    Finds squares in a binary image.

    Args:
        binary_img: Input binary image as a NumPy array (0s and 255s).

    Returns:
        A list of square contours.
    """
    height, width = binary_img.shape
    squares = []
    visited_pixels = np.zeros_like(binary_img, dtype=bool)

    for y in range(height):
        for x in range(width):
            if binary_img[y, x] == 1 and not visited_pixels[y, x]:
                # Consider this as a potential top-left corner of a square
                for size in range(5, min(height - y, width - x)):  # Minimum size of 5 to avoid noise
                    # Calculate potential other corners
                    top_right_x = x + size
                    bottom_left_y = y + size
                    bottom_right_x = x + size
                    bottom_right_y = y + size
                    # Check if potential corners exist within bounds and are white
                    if (top_right_x < width and binary_img[y, top_right_x] == 1 and
                        bottom_left_y < height and binary_img[bottom_left_y, x] == 1 and
                        bottom_right_x < width and bottom_right_y < height and binary_img[bottom_right_y, bottom_right_x] == 1):

                        # Verify the sides are mostly filled (allowing for connections)
                        top_edge = binary_img[y, x : top_right_x + 1]
                        bottom_edge = binary_img[bottom_left_y, x : bottom_right_x + 1]
                        left_edge = binary_img[y : bottom_left_y + 1, x]
                        right_edge = binary_img[y : bottom_right_y + 1, top_right_x]

                        top_filled = np.sum(top_edge == 1) >= (size * 0.8)  # At least 80% filled
                        bottom_filled = np.sum(bottom_edge == 1) >= (size * 0.8)
                        left_filled = np.sum(left_edge == 1) >= (size * 0.8)
                        right_filled = np.sum(right_edge == 1) >= (size * 0.8)

                        if top_filled and bottom_filled and left_filled and right_filled:
                            square_coords = [(x, y), (top_right_x, y), (top_right_x, bottom_right_y), (x, bottom_left_y)]
                            squares.append(np.array([np.array(coord) for coord in square_coords]))

                            # Mark the pixels of this square as visited to avoid duplicates
                            for sy in range(y, bottom_right_y + 1):
                                for sx in range(x, bottom_right_x + 1):
                                    if 0 <= sy < height and 0 <= sx < width:
                                        visited_pixels[sy, sx] = True
                            break  # Move to the next potential top-left corner

    return squares

def removeContainedSquares(squares):
    """
    Removes squares that are fully contained within other squares.

    Args:
        squares: A list of square contours.

    Returns:
        A list of square contours with contained squares removed.
    """
    filtered_squares = []
    n = len(squares)
    is_contained = [False] * n

    for i in range(n):
        if is_contained[i]:
            continue  # Skip if already marked as contained
        for j in range(n):
            if i == j:
                continue

            # Check if squares[i] is contained in squares[j]
            all_points_inside = True
            for point_array in squares[i]:  # Iterate over the rows (points)
                pt = tuple(point_array) # Extract the point tuple
                pt = tuple([int(round(pt[0]) ), int(round( pt[1] )) ])

                result = cv2.pointPolygonTest(squares[j], pt, False)
                if result  < 0:
                    all_points_inside = False
                    break

            if all_points_inside:
                is_contained[i] = True
                break  # No need to check further for this square

    for i in range(n):
        if not is_contained[i]:
            filtered_squares.append(squares[i])

    return filtered_squares

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

from typing import TypedDict, List, Dict, Any, Type, Union
import json
from enum import Enum

def typed_dict_to_string(
    typed_dict_class,
    include_type_hints: bool = True,
    pretty_print: bool = False,
    include_docstring: bool = True,
    _indent_level: int = 0,  # Internal parameter for recursion
) -> str:
    """
    Converts a TypedDict class to a string representation, optionally including
    type hints, docstrings and pretty-printing. Handles nested TypedDicts
    and other type annotations recursively.

    Args:
        typed_dict_class: The TypedDict class to convert.
        include_type_hints: Whether to include type hints in the string
                           representation. Defaults to True.
        pretty_print: Whether to pretty-print the output (add indentation
                      and newlines).  Defaults to False.
        include_docstring: Whether to include the docstring in the output string. Defaults to True
        _indent_level: (Internal) Current indentation level.

    Returns:
        A string representation of the TypedDict class.

    Raises:
        TypeError: If typed_dict_class is not a TypedDict.
        ValueError: if total=False is provided with a TypedDict.
    """

    if not (isinstance(typed_dict_class, type) and issubclass(typed_dict_class, dict)):
        raise TypeError("typed_dict_class must be a TypedDict class.")

    # if not getattr(typed_dict_class, "__total__", True):  # Check for total=False
    #     raise ValueError(
    #         "The TypedDict must use total=True. It's required for a complete string representation."
    #     )

    indent = "    " * _indent_level if pretty_print else ""
    next_indent = "    " * (_indent_level + 1) if pretty_print else ""
    lines = []

    lines.append(f"{indent}class {typed_dict_class.__name__}:")

    if include_docstring and typed_dict_class.__doc__:
        docstring_lines = typed_dict_class.__doc__.splitlines()
        if pretty_print:
            lines.append(next_indent + '"""')
            lines.extend([next_indent + line for line in docstring_lines])
            lines.append(next_indent + '"""')
        else:
            lines.append(
                next_indent
                + '"""'
                + typed_dict_class.__doc__.replace("\n", " ")
                + '"""'
            )

    if not include_type_hints:
        if not hasattr(typed_dict_class, "__annotations__"):
            return f"{indent}class {typed_dict_class.__name__}: pass"

        for key in typed_dict_class.__annotations__.keys():
            lines.append(f"{next_indent}{key}")
        return "\n".join(lines)

    annotations = typed_dict_class.__annotations__
    for key, value in annotations.items():
        type_str = _get_type_string(
            value, include_type_hints, pretty_print, include_docstring, _indent_level + 1
        )
        lines.append(f"{next_indent}{key}: {type_str}")

    return "\n".join(lines)


def _get_type_string(
    type_hint: Any,
    include_type_hints: bool,
    pretty_print: bool,
    include_docstring: bool,
    indent_level: int,
) -> str:
    """
    Recursively generates string representations for type hints, handling
    TypedDicts, Lists, Dicts, Unions, Enums, and basic types.

    Args:
        type_hint: The type hint to convert.
        include_type_hints: Whether to include type hints.
        pretty_print: Whether to pretty-print.
        include_docstring: Whether to include the docstring.
        indent_level: Current indentation level.

    Returns:
        String representation of the type hint.
    """
    indent = "    " * indent_level if pretty_print else ""

    if isinstance(type_hint, type) and issubclass(type_hint, dict):  # TypedDict
        return (
            "\n" + typed_dict_to_string(
                type_hint,
                include_type_hints,
                pretty_print,
                include_docstring,
                indent_level,
            )
            if pretty_print
            else typed_dict_to_string(
                type_hint,
                include_type_hints,
                pretty_print,
                include_docstring,
                indent_level,
            )
        )
    elif isinstance(type_hint, type) and issubclass(type_hint, Enum):  # Enum
        return type_hint.__name__
    elif hasattr(type_hint, "__origin__"):  # For generic types like List, Dict, Union
        origin = type_hint.__origin__
        args = type_hint.__args__

        if origin is list:
            arg_str = _get_type_string(
                args[0], include_type_hints, pretty_print, include_docstring, indent_level
            )
            return f"list[{arg_str}]"
        elif origin is dict:
            key_str = _get_type_string(
                args[0], include_type_hints, pretty_print, include_docstring, indent_level
            )
            value_str = _get_type_string(
                args[1], include_type_hints, pretty_print, include_docstring, indent_level
            )
            return f"dict[{key_str}, {value_str}]"
        elif origin is Union:
            arg_strs = [
                _get_type_string(
                    arg, include_type_hints, pretty_print, include_docstring, indent_level
                )
                for arg in args
            ]
            return " | ".join(arg_strs)
        else:
            return str(type_hint).replace("typing.", "") # Handle other generic types if needed.
    elif isinstance(type_hint, str):  # ForwardRef (string-based type hint)
        return type_hint
    else:  # Basic types (int, str, bool, etc.)
        return str(type_hint).replace("typing.", "")
    
    
from pydantic import BaseModel, Field
from typing import Optional, List, get_origin, get_args



def base_model_to_schema_string(model_class: type[BaseModel], indent_level=0) -> str:
    """
    Converts a Pydantic BaseModel class schema to a nicely formatted string for AI parsing.
    Handles nested BaseModels and lists of BaseModels or primitive types.
    """
    schema_string = ""
    indent = ""
    if indent_level != 0:
        schema_string += f"{indent}{model_class.__name__}:\n"
        indent = "  " * (indent_level - 1)
    
    for field_name, field in model_class.__fields__.items():
        field_type = field.annotation
        type_str = ""

        origin = get_origin(field_type)
        args = get_args(field_type)

        if origin is list:
            if args:
                arg_type = args[0]
                if isinstance(arg_type, type) and issubclass(arg_type, BaseModel):
                    type_str = f"list[{arg_type.__name__}]"
                else:
                    type_str = f"list[{arg_type.__name__ if hasattr(arg_type, '__name__') else str(arg_type)}]" # handle typing.Optional, etc
            else:
                type_str = "list" # should not happen in pydantic usually
        elif isinstance(field_type, type) and issubclass(field_type, BaseModel):
            type_str = field_type.__name__
        else:
            type_str = field_type.__name__ if hasattr(field_type, '__name__') else str(field_type) # handle typing.Optional, etc

        schema_string += f"{indent}  {field_name}: {type_str}\n"

        if origin is list:
            if args:
                arg_type = args[0]
                if isinstance(arg_type, type) and issubclass(arg_type, BaseModel):
                    schema_string += base_model_to_schema_string(arg_type, indent_level + 1)
        elif isinstance(field_type, type) and issubclass(field_type, BaseModel):
            schema_string += base_model_to_schema_string(field_type, indent_level + 1)
    return schema_string
    """
    Generates a human-readable schema string from a Pydantic BaseModel,
    suitable for AI parsing, handling nested models and lists.
    """
    indent = "  " * indent_level
    schema_str = f"{indent}Model: {model.__class__.__name__}\n{indent}Fields:\n"
    for field_name, field_info in model.model_fields.items():
        field_type = field_info.annotation
        description = field_info.description or ""
        required = field_info.is_required()

        schema_str += f"{indent}  - Field: {field_name}\n"
        schema_str += f"{indent}    Type: {get_type_string(field_type)}\n" # Use get_type_string
        if description:
            schema_str += f"{indent}    Description: {description}\n"
        schema_str += f"{indent}    Required: {'Yes' if required else 'No'}\n"

        origin_type = get_origin(field_type)
        args_type = get_args(field_type)

        if origin_type is list: # Handle List types
            if args_type: # List with a specified type argument
                list_item_type = args_type[0]
                if issubclass(list_item_type, BaseModel) and list_item_type != BaseModel: # Check if list item is a BaseModel
                    schema_str += f"{indent}    List Item Schema:\n"
                    schema_str += model_to_schema_string(list_item_type(), indent_level + 3) # Recursive call for list item model
            else:
                schema_str += f"{indent}    Note: List item type is not specified in type hints.\n"

        elif issubclass(field_type, BaseModel) and field_type != BaseModel and field_type != model.__class__: # Handle nested BaseModel
            schema_str += f"{indent}    Nested Model Schema:\n"
            schema_str += model_to_schema_string(field_type(), indent_level + 3) # Recursive call for nested model

        schema_str += "\n" # Separate fields with a newline

    return schema_str