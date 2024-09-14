from PIL import Image, ImageEnhance                                                                
import sys

img = Image.open("image_output/outfile_i0_student0_0.png")
img = img.convert("RGBA")

pixdata = img.load()

# Clean the background noise, if color != white, then set to black.

# REMOVE RED PEN
for y in range(img.size[1]):
    for x in range(img.size[0]):
        r, g, b, a = pixdata[x, y]
        
        # REMOVE RED PEN
        if (r - g > 20 and
            r - b > 20 and
            r > 200) :
            
            radius = 2
            
            for i in range(2*radius):
                for j in range(2*radius):
                    pixdata[x + i - radius, y + j - radius] = (255, 255, 255)

# img.convert("L")

# SHARPEN
enhancer = ImageEnhance.Sharpness(img)
img = enhancer.enhance(10)


img.save('color_correction_output/test.png')