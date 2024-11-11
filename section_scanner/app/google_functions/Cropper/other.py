import cv2
import imutils
from skimage.filters import threshold_local
import numpy as np

def order_points(pts):
   # initializing the list of coordinates to be ordered
   rect = np.zeros((4, 2), dtype = "float32")

   s = pts.sum(axis = 1)

   # top-left point will have the smallest sum
   rect[0] = pts[np.argmin(s)]

   # bottom-right point will have the largest sum
   rect[2] = pts[np.argmax(s)]

   '''computing the difference between the points, the
   top-right point will have the smallest difference,
   whereas the bottom-left will have the largest difference'''
   diff = np.diff(pts, axis = 1)
   rect[1] = pts[np.argmin(diff)]
   rect[3] = pts[np.argmax(diff)]

   # returns ordered coordinates
   return rect

def perspective_transform(image, pts):
   # unpack the ordered coordinates individually
   rect = order_points(pts)
   (tl, tr, br, bl) = rect

   '''compute the width of the new image, which will be the
   maximum distance between bottom-right and bottom-left
   x-coordinates or the top-right and top-left x-coordinates'''
   widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
   widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
   maxWidth = max(int(widthA), int(widthB))

   '''compute the height of the new image, which will be the
   maximum distance between the top-left and bottom-left y-coordinates'''
   heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
   heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
   maxHeight = max(int(heightA), int(heightB))

   '''construct the set of destination points to obtain an overhead shot'''
   dst = np.array([
      [0, 0],
      [maxWidth - 1, 0],
      [maxWidth - 1, maxHeight - 1],
      [0, maxHeight - 1]], dtype = "float32")

   # compute the perspective transform matrix
   transform_matrix = cv2.getPerspectiveTransform(rect, dst)

   # Apply the transform matrix
   warped = cv2.warpPerspective(image, transform_matrix, (maxWidth, maxHeight))

   # return the warped image
   return (warped, heightA, heightB, widthA, widthB)



def scan(original_img):
    copy = original_img.copy()

    # The resized height in hundreds
    ratio = original_img.shape[0] / 500.0
    img_resize = imutils.resize(original_img, height=500)

        
    gray_image = cv2.cvtColor(img_resize, cv2.COLOR_BGR2GRAY)

    blurred_image = cv2.GaussianBlur(gray_image, (5, 5), 0)
    edged_img = cv2.Canny(blurred_image, 75, 200)
    
    cnts, _ = cv2.findContours(edged_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]

    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        if len(approx) == 4:
            doc = approx
            break
        
    warped_image, heightA, heightB, widthA, widthB = perspective_transform(copy, doc.reshape(4, 2) * ratio)
    
    # image must take at least 1/2 of the image
    height, width, scale = copy.shape
    
    if ((heightA / height < 1/2) 
        or (heightB / height < 1/2) 
        or (widthA / width < 1/2) 
        or (widthB / width < 1/2) 
    ):
        return original_img
        
    
    # warped_image = cv2.cvtColor(warped_image, cv2.COLOR_BGR2GRAY)
    
    # T = threshold_local(warped_image, 11, offset=10, method="gaussian")
    # warped = (warped_image > T).astype("uint8") * 255
    
    return warped_image