import cv2

def check_image_quality(image_path):
    """
    Returns:
        score  : Blur score
        status : Good / Acceptable / Blurry / Very Blurry
    """

    img = cv2.imread(image_path)

    if img is None:
        return 0, "Image Not Found"

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Laplacian variance (higher = sharper)
    score = cv2.Laplacian(gray, cv2.CV_64F).var()

    if score > 150:
        status = "Good"
    elif score > 80:
        status = "Acceptable"
    elif score > 40:
        status = "Blurry"
    else:
        status = "Very Blurry"

    return score, status