import cv2
import os
import numpy as np
from tqdm import tqdm

def align_images(template_path, image_path, max_features=10000, good_match_percent=100):
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if template is None or image is None:
        print(f'Failed to load image: {image_path}')
        return False
    orb = cv2.ORB_create(max_features)
    keypoints1, descriptors1 = orb.detectAndCompute(template, None)
    keypoints2, descriptors2 = orb.detectAndCompute(image, None)
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = matcher.match(descriptors1, descriptors2)
    matches = sorted(matches, key=lambda x: x.distance)
    num_good_matches = min(len(matches), max(1, int(len(matches) * good_match_percent)))
    matches = matches[:num_good_matches]
    points1 = np.float32([keypoints1[match.queryIdx].pt for match in matches]).reshape(-1, 1, 2)
    points2 = np.float32([keypoints2[match.trainIdx].pt for match in matches]).reshape(-1, 1, 2)
    h, _ = cv2.findHomography(points2, points1, cv2.RANSAC, 5.0)
    height, width = template.shape
    aligned_image = cv2.warpPerspective(image, h, (width, height))
    cv2.imwrite(image_path, aligned_image)
    return True

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python align.py <template_image> <image_dir>")
        sys.exit(1)
    template_image = sys.argv[1]
    image_dir = sys.argv[2]

    # Recursively collect all F.jpg files
    image_files = []
    for root, dirs, files in os.walk(image_dir):
        for file in files:
            if file.lower().endswith('f.jpg'):
                image_files.append(os.path.join(root, file))

    print(f'Aligning {len(image_files)} images...')
    for image_file in tqdm(image_files):
        align_images(template_image, image_file)

    # Create alignment done marker in the base directory
    with open(os.path.join(image_dir, 'alignment_done.txt'), 'w') as f:
        f.write('Alignment complete.')

    print('Alignment complete.')