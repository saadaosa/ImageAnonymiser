import cv2


def blur_boxes(image, boxes, kernel):

  for box in boxes:
    x1, y1, x2, y2 = box
    region = image[y1:y2, x1:x2]
    blur = cv2.GaussianBlur(region, kernel, 0) 
    image[y1:y2, x1:x2] = blur

def blur_pixels(image, pixel_indices, kernel):

  blur = cv2.GaussianBlur(image, kernel, 0) 
  image[pixel_indices] = blur[pixel_indices]