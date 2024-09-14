b = box.split(' ')
    # char = b[0]  # Detected character
    # x_start, y_start = int(b[1]), int(b[2])
    # x_end, y_end = int(b[3]), int(b[4])
    # if (y_start < 160 or True):
    #     # OpenCV uses (x, y) coordinates with the origin at the top-left,
    #     # so we need to invert the y-coordinates from Tesseract
    #     # Draw a rectangle around the detected character (optional)
    #     cv2.rectangle(img, (x_start, h - y_start), (x_end, h - y_end), (0, 255, 0), 2)

    #     # Write the character at the top-left corner of the bounding box
    #     # Adjust the y-coordinate to slightly offset the text vertically within the box
    #     font_scale = 1  # You can adjust the scale if needed
    #     font_thickness = 2
    #     cv2.putText(img, char, (x_start, h - y_start), cv2.FONT_HERSHEY_SIMPLEX, 
    #                 font_scale, (255, 0, 0), font_thickness)