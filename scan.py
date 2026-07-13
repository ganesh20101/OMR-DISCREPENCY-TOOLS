import cv2
import numpy as np
import json
import csv
import os
import sys

class OMRScanner:
    def __init__(self, template_file, image_dir, output_csv):
        self.template_file = template_file
        self.image_dir = image_dir
        self.output_csv = output_csv
        self.qpseries_region = None
        self.question_regions = []
        self.roll_number_regions = []
        self.qbno_regions = []
        self.load_template()

    def load_template(self):
        with open(self.template_file, 'r') as file:
            template_data = json.load(file)
            self.qpseries_region = template_data.get('qpseries_region', None)
            self.question_regions = template_data.get('question_regions', [])
            self.roll_number_regions = template_data.get('roll_number_regions', [])
            self.qbno_regions = template_data.get('qbno_regions', [])
        print(f"Template loaded from {self.template_file}")

    def detect_shaded_option_qp(self, cropped_image):
        if cropped_image is None or not isinstance(cropped_image, np.ndarray):
            return 'X'
        _, binary_image = cv2.threshold(cropped_image, 50, 255, cv2.THRESH_BINARY_INV)
        height, width = cropped_image.shape
        option_height = height // 4
        option_regions = [
            (0, 0, width, option_height),
            (0, option_height, width, 2 * option_height),
            (0, 2 * option_height, width, 3 * option_height),
            (0, 3 * option_height, width, height)
        ]
        detected_options = []
        for idx, (x1, y1, x2, y2) in enumerate(option_regions):
            option_mask = np.zeros((height, width), dtype=np.uint8)
            cv2.rectangle(option_mask, (x1, y1), (x2, y2), 255, -1)
            intersection = cv2.bitwise_and(binary_image, binary_image, mask=option_mask)
            option_contours, _ = cv2.findContours(intersection, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if option_contours:
                detected_options.append(chr(65 + idx))
        if len(detected_options) == 0:
            return 'X'
        elif len(detected_options) > 1:
            return '*'
        else:
            return detected_options[0]

    def detect_shaded_option(self, cropped_image):
        blurred_image = cv2.GaussianBlur(cropped_image, (5, 5), 0)
        _, binary_image = cv2.threshold(blurred_image, 100, 255, cv2.THRESH_BINARY_INV)
        height, width = cropped_image.shape
        option_width = width // 4
        option_regions = [
            (0, 0, option_width, height),
            (option_width, 0, 2 * option_width, height),
            (2 * option_width, 0, 3 * option_width, height),
            (3 * option_width, 0, width, height)
        ]
        detected_options = []
        for idx, (x1, y1, x2, y2) in enumerate(option_regions):
            option_mask = np.zeros_like(binary_image)
            cv2.rectangle(option_mask, (x1, y1), (x2, y2), 255, -1)
            intersection = cv2.bitwise_and(binary_image, binary_image, mask=option_mask)
            option_contours, _ = cv2.findContours(intersection, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for contour in option_contours:
                area = cv2.contourArea(contour)
                if area > 80:
                    detected_options.append(chr(ord('A') + idx))
                    break
        if len(detected_options) == 0:
            return 'X'
        elif len(detected_options) > 1:
            return '*'
        else:
            return detected_options[0]

    def detect_shaded_roll_number(self, cropped_image):
        blurred_image = cv2.GaussianBlur(cropped_image, (5, 5), 0)
        _, binary_image = cv2.threshold(blurred_image, 100, 255, cv2.THRESH_BINARY_INV)
        height, width = cropped_image.shape
        bubble_regions = []
        for i in range(10):
            y_start = i * height // 10
            y_end = (i + 1) * height // 10
            bubble_regions.append((0, y_start, width, y_end))
        detected_digits = []
        for digit, (x1, y1, x2, y2) in enumerate(bubble_regions):
            bubble_mask = np.zeros_like(binary_image)
            cv2.rectangle(bubble_mask, (x1, y1), (x2, y2), 255, -1)
            intersection = cv2.bitwise_and(binary_image, binary_image, mask=bubble_mask)
            bubble_contours, _ = cv2.findContours(intersection, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if bubble_contours:
                for contour in bubble_contours:
                    area = cv2.contourArea(contour)
                    if area > 130:
                        detected_digits.append(str(digit))
                        break
        if len(detected_digits) == 0:
            return 'X'
        elif len(detected_digits) > 1:
            return '*'
        else:
            return detected_digits[0]

    def detect_shaded_qbno(self, cropped_image):
        blurred_image = cv2.GaussianBlur(cropped_image, (5, 5), 0)
        _, binary_image = cv2.threshold(blurred_image, 100, 255, cv2.THRESH_BINARY_INV)
        height, width = cropped_image.shape
        bubble_regions = []
        for i in range(10):
            y_start = i * height // 10
            y_end = (i + 1) * height // 10
            bubble_regions.append((0, y_start, width, y_end))
        detected_digits = []
        for digit, (x1, y1, x2, y2) in enumerate(bubble_regions):
            bubble_mask = np.zeros_like(binary_image)
            cv2.rectangle(bubble_mask, (x1, y1), (x2, y2), 255, -1)
            intersection = cv2.bitwise_and(binary_image, binary_image, mask=bubble_mask)
            bubble_contours, _ = cv2.findContours(intersection, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if bubble_contours:
                for contour in bubble_contours:
                    area = cv2.contourArea(contour)
                    if area > 130:
                        detected_digits.append(str(digit))
                        break
        if len(detected_digits) == 0:
            return 'X'
        elif len(detected_digits) > 1:
            return '*'
        else:
            return detected_digits[0]

    def scan_images(self):
        csv_data = []
        image_paths = []
        
        # Recursively collect all F.jpg files
        image_files = []
        for root, dirs, files in os.walk(self.image_dir):
            for file in files:
                if file.lower().endswith('f.jpg'):
                    image_files.append(os.path.join(root, file))
        
        if not image_files:
            print(f"No F.jpg files found in {self.image_dir} or its subfolders")
            return []
        
        print(f"Found {len(image_files)} images to process")
        for image_path in image_files:
            image_paths.append(image_path)
            cv_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if cv_image is None:
                print(f"Failed to load image: {image_path}")
                continue
            qpseries_response = self.detect_shaded_option_qp(
                cv_image[self.qpseries_region[1]:self.qpseries_region[3],
                        self.qpseries_region[0]:self.qpseries_region[2]]
            )
            roll_number_responses = [
                self.detect_shaded_roll_number(cv_image[y:y+h, x:x+w])
                for _, x, y, w, h in self.roll_number_regions
            ]
            question_responses = [
                self.detect_shaded_option(cv_image[y:y+h, x:x+w])
                for _, x, y, w, h in self.question_regions
            ]
            qbno_responses = [
                self.detect_shaded_qbno(cv_image[y:y+h, x:x+w])
                for _, x, y, w, h in self.qbno_regions
            ]
            roll_number_str = ''.join(roll_number_responses)
            qbno_str = ''.join(qbno_responses)
            row = [roll_number_str, qbno_str, qpseries_response] + question_responses + [image_path]
            csv_data.append(row)
            print(f"Processed: {os.path.basename(image_path)} - ROLLNO: {roll_number_str}, QBNO: {qbno_str}, QPSERIES: {qpseries_response}")
        
        if csv_data:
            with open(self.output_csv, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                header = ['ROLLNO', 'QBNO', 'QPSERIES'] + [f'A{i}' for i in range(1, len(self.question_regions) + 1)] + ['Front side Image']
                writer.writerow(header)
                for row in csv_data:
                    writer.writerow(row)
            print(f"Responses saved to {self.output_csv}")
            print(f"Total images processed: {len(csv_data)}")
        else:
            print("No data to save")
        return csv_data

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python omr_scan_auto.py <template_file> <image_dir> <output_csv>")
        sys.exit(1)
    template_file = sys.argv[1]
    image_dir = sys.argv[2]
    output_csv = sys.argv[3]
    try:
        scanner = OMRScanner(template_file, image_dir, output_csv)
        scanner.scan_images()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)