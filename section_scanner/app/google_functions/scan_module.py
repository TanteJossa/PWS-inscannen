from PIL import Image, ImageEnhance, ImageFont, ImageDraw                                                           
import sys
import os
import copy

from helpers import (
    clamp,
    get_black_square_data,
)

input_dir = "temp_image/"
output_dir = "temp_image_output/"


def extract_red_pen(id):
    # remove .png
    
    img = Image.open(input_dir + id + '.png')
    img = img.convert("RGBA")


    clean_pixdata = img.load()
    clean_pixdata2 = img.copy().load()
    red_pen_image = Image.new('RGBA', (img.width, img.height), color=(0,0,0,0))
    red_pen_pixdata = red_pen_image.load()

    # Clean the background noise, if color != white, then set to black.

    radius = 2

    # REMOVE RED PEN
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b, a = clean_pixdata[x, y]

            
            # REMOVE RED PEN
            if (r - g > 20 and
                r - b > 20 and
                r > 200) :
                

                for i in range(2*radius):
                    for j in range(2*radius):
                        red_pen_pixdata[x + i - radius, y + j - radius] = clean_pixdata2[x + i - radius, y + j - radius]

                        # copy the old red pen values
                        clean_pixdata[x + i - radius, y + j - radius] = (255, 255, 255)
                

    # img.convert("L")

    # SHARPEN
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(10)

    try:
        os.makedirs(output_dir+id)
    except:
        pass

    img.save(output_dir + id +'/original.png')

    red_pen_image.save(output_dir+id+'/red_pen.png')







def detect_squares(id):

    img = Image.open(input_dir + id + '.png')


    # Get the heights and start positions of the black squares
    black_square_info, gray_img, contour_image = get_black_square_data(img)
    # gray_img.save(output_dir+image_dir+'_bw.png')
    # contour_image.save(output_dir+image_dir+'_countors.png')
    
    # filter too high
    black_square_info = [x for x in black_square_info if x[3] - x[2] > 10]

    # sort
    black_square_info.sort(key=lambda x: x[0])

    
    # Load the original image
    draw = ImageDraw.Draw(img)
    
    # Define the box color and text color
    box_color = (255, 0, 0)  # Red color
    text_color = (255, 0, 0) # Red text
    
    
    # Load a font for the height labels
    # Using default font as PIL may not always have a specific font path on the system
    try:
        font = ImageFont.truetype("arial.ttf", 15)
    except IOError:
        font = ImageFont.load_default()

    # Get image width (to make the box span across the image width)
    img_width, img_height = img.size

    # Overlay each square with a red box and label it with its height
    for start, height,x_min,x_max in black_square_info:
        # Draw a red rectangle around each black square
        draw.rectangle([x_min, start, x_max, start + height], outline=box_color, width=2)
        
        # Add the height label next to the square
        draw.text((img_width - 50, start - 15), f"{start}px", fill=text_color, font=font)
    
    # Save the resulting image
    img.save(output_dir+id+'.png')
    
    return black_square_info



def sectionize(id,square_data):
    
    image = Image.open(input_dir+id+ '.png')
    
    square_heights = [square[0] for square in square_data]
    square_x_max = [square[3] for square in square_data]
    square_heights.append(image.height)

    for index, h_break in enumerate(square_heights):
        
        if (index >= len(square_heights) - 1 ):
            continue
        
        y = clamp(h_break - 7, 0, image.height - 1)
        next_y = clamp(square_heights[index+1] - 5, 0, image.height - 1)
        
        # min height and fix
        if (next_y < y or next_y - y < 30):
            continue
        
        # kantlijn, boven, einde van pagina, beneden grens
        crop = (0, y, image.width, next_y)
        
        section_image = image.copy()
        
        cropped = section_image.crop(crop)        

        # section_image.show()
        # section_file_name = filenameify(h_break["description"])+".png"
        
        sections_output_dir = output_dir + id + '/'
        try:
            os.makedirs(sections_output_dir)
        except:
            pass
        
        section_name = id+"_"+str(index)
        cropped.save(sections_output_dir+section_name+'.png')

def section_question(id):
    image = Image.open(input_dir+id+ '.png')

    pass