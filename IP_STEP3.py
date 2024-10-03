import tkinter as tk
from tkinter import filedialog, ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import cv2
import numpy as np
import json
import csv
import os
import ctypes
from tqdm import tqdm
import threading

class OMRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OMR Image Processing Tool COPYRIGHT @ GANESH 2024")
        # Check password before initializing the app
        if not self.check_password():
            self.root.destroy()
            return
        # Load and display background image
        self.background_image = Image.open(r"C:\Users\HP\Downloads\omr.jpg")  # Replace with your image path
        self.background_photo = ImageTk.PhotoImage(self.background_image)
        self.background_label = tk.Label(root, image=self.background_photo)
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Canvas for displaying the image
        self.canvas = tk.Canvas(root)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Vertical scrollbar
        self.scroll_y = ttk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.scroll_y.pack(side=tk.RIGHT, fill="y")

        # Horizontal scrollbar
        self.scroll_x = ttk.Scrollbar(root, orient="horizontal", command=self.canvas.xview)
        self.scroll_x.pack(side=tk.BOTTOM, fill="x")

        self.canvas.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)

        # Bind mouse events to canvas for cropping
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        # Button to load image
        self.load_button = ttk.Button(root, text="Load Image", command=self.load_image)
        self.load_button.pack(side=tk.TOP)

        # Button to process cropped regions
        self.process_button = ttk.Button(root, text="Process Cropped Regions", command=self.process_cropped_regions)
        self.process_button.pack(side=tk.TOP)

        # Mode selection radio buttons
        self.mode_selection = tk.StringVar(value="QPSERIES")  # Default mode is QPSERIES
        modes_frame = ttk.Frame(root)
        modes_frame.pack(side=tk.TOP, pady=10)
        
        ttk.Radiobutton(modes_frame, text="QPSERIES", variable=self.mode_selection, value="QPSERIES").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(modes_frame, text="ROLLNO", variable=self.mode_selection, value="ROLLNO").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(modes_frame, text="response", variable=self.mode_selection, value="response").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(modes_frame, text="QBNO", variable=self.mode_selection, value="QBNO").pack(side=tk.LEFT, padx=10)

        # Entry field and label for max roll number input
        self.max_roll_number_label = tk.Label(root, text="Max Roll Numbers:")
        self.max_roll_number_label.pack(side=tk.TOP, pady=5)
        
        self.max_roll_number_entry = ttk.Entry(root)
        self.max_roll_number_entry.pack(side=tk.TOP)

        # Label and entry for max QBNO input
        self.max_qbno_label = tk.Label(root, text="Max QBNO Numbers:")
        self.max_qbno_label.pack(side=tk.TOP, pady=5)
        
        self.max_qbno_entry = ttk.Entry(root)
        self.max_qbno_entry.pack(side=tk.TOP)

        # Label to display QBNO count
        self.qbno_count_label = tk.Label(root, text="QBNO Count: 0", padx=10)
        self.qbno_count_label.pack(side=tk.TOP)

        # Labels to display counts
        self.qpseries_count_label = tk.Label(root, text="QPSERIES Count: 0", padx=10)
        self.qpseries_count_label.pack(side=tk.TOP)

        self.roll_number_count_label = tk.Label(root, text="ROLLNO Count: 0", padx=10)
        self.roll_number_count_label.pack(side=tk.TOP)

        self.response_count_label = tk.Label(root, text="Response Count: 0", padx=10)
        self.response_count_label.pack(side=tk.TOP)
        # Button to save template
        self.save_template_button = ttk.Button(root, text="Save Template", command=self.save_template)
        self.save_template_button.pack(side=tk.TOP)

        # Button to load template and scan multiple images
        self.scan_button = ttk.Button(root, text="Scan Multiple Images", command=self.scan_multiple_images)
        self.scan_button.pack(side=tk.TOP)

        # Entry for template image path
        tk.Label(root, text="Template Image:").pack(pady=5)
        self.template_entry = tk.Entry(root, width=50)
        self.template_entry.pack(pady=5)
        tk.Button(root, text="Browse", command=self.upload_template).pack(pady=5)

        # Entry for image directory path
        tk.Label(root, text="Image Directory:").pack(pady=5)
        self.image_dir_entry = tk.Entry(root, width=50)
        self.image_dir_entry.pack(pady=5)
        tk.Button(root, text="Browse", command=self.select_image_directory).pack(pady=5)

        # Button to align images
        tk.Button(root, text="Align Images", command=self.align_images_in_directory).pack(pady=20)

        # Label for showing loading message
        self.loading_label = tk.Label(root, text="", font=("Helvetica", 12))

        # Initialize variables
        self.regions = []
        self.qpseries_region = None  # Variable to store QPSERIES region coordinates
        self.roll_number_regions = []  # Variable to store roll number region coordinates
        self.qbno_regions = []
        self.current_question = 1  # Start with question 1
        self.current_roll_number = 1  # Start with roll number 1
        self.current_qbno = 1
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.image = None
        self.tk_image = None
        self.cv_image = None

    def check_password(self):
        # Function to check password before allowing access
        password = simpledialog.askstring("Password", "Enter password:", show='*')
        if password == "OmrScanning@2024":
            return True
        else:
            messagebox.showerror("Access Denied", "Incorrect password. Exiting application.")
            return False


    def load_image(self):
        # Load an image using file dialog
        file_path = filedialog.askopenfilename()
        if file_path:
            self.cv_image = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
            self.image = Image.fromarray(self.cv_image)
            self.tk_image = ImageTk.PhotoImage(self.image)

            # Update the canvas with the new image
            self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def on_button_press(self, event):
        # Start the cropping process based on the selected mode
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        
        # Determine the color for the rectangle based on the selected mode
        if self.mode_selection.get() == "QPSERIES":
            outline_color = 'red'
        elif self.mode_selection.get() == "ROLLNO":
            outline_color = 'blue'
        elif self.mode_selection.get() == "response":
            outline_color = 'green'
        elif self.mode_selection.get() == "QBNO":
            outline_color = 'red'
        else:
            outline_color = 'red'  # Default to red if mode not recognized
        
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline=outline_color)

    def on_move_press(self, event):
        # Update the rectangle as the mouse moves
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        # Finalize the cropped region and store its coordinates based on the selected mode
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)

        if self.mode_selection.get() == "QPSERIES":
            # First click defines the QPSERIES region
            self.qpseries_region = (int(self.start_x), int(self.start_y), int(end_x), int(end_y))
            self.qpseries_count_label.config(text=f"QPSERIES Count: {len(self.qpseries_region)}")
        elif self.mode_selection.get() == "ROLLNO":
            # Crop roll number regions based on the dynamically set max_roll_number
            max_roll_number = int(self.max_roll_number_entry.get())
            if self.current_roll_number <= max_roll_number:
                self.roll_number_regions.append((self.current_roll_number, int(self.start_x), int(self.start_y), int(end_x - self.start_x), int(end_y - self.start_y)))
                self.roll_number_count_label.config(text=f"ROLLNO Count: {self.current_roll_number}")
                self.current_roll_number += 1
                if self.current_roll_number > max_roll_number:
                    messagebox.showwarning("Warning", f"You have defined the maximum number of roll number regions ({max_roll_number}).")
            else:
                messagebox.showwarning("Warning", f"You have defined the maximum number of roll number regions ({max_roll_number}).")
        elif self.mode_selection.get() == "QBNO":
            # Crop roll number regions based on the dynamically set max_roll_number
            max_qbno = int(self.max_qbno_entry.get())
            if self.current_qbno <= max_qbno:
                self.qbno_regions.append((self.current_qbno, int(self.start_x), int(self.start_y), int(end_x - self.start_x), int(end_y - self.start_y)))
                self.qbno_count_label.config(text=f"QB Count: {self.current_qbno}")
                self.current_qbno += 1
                if self.currrent_qbno > max_qbno:
                    messagebox.showwarning("Warning", f"You have defined the maximum number of QB number regions ({max_qbno}).")
            else:
                messagebox.showwarning("Warning", f"You have defined the maximum number of QB number regions ({max_qbno}).")
        elif self.mode_selection.get() == "response":
            # Second click defines a response region
            self.regions.append((self.current_question, int(self.start_x), int(self.start_y), int(end_x - self.start_x), int(end_y - self.start_y)))
            self.response_count_label.config(text=f"Response Count: {self.current_question}")
            self.current_question += 1  # Move to the next question number
        
        self.start_x = None
        self.start_y = None
        self.rect = None
    def process_cropped_regions(self):
        if self.cv_image is None:
            print("No image loaded.")
            return

        if self.qpseries_region is None:
            print("No QPSERIES region selected.")
            return

        # Detect shaded options for QPSERIES region
        qpseries_responses = self.detect_shaded_option_qp(self.cv_image[self.qpseries_region[1]:self.qpseries_region[3], self.qpseries_region[0]:self.qpseries_region[2]])

        # Detect roll numbers
        roll_number_responses = [self.detect_shaded_roll_number(self.cv_image[y:y+h, x:x+w]) for _, x, y, w, h in self.roll_number_regions]

        # Detect shaded options for all cropped A1 regions
        responses = [self.detect_shaded_option(self.cv_image[y:y+h, x:x+w]) for _, x, y, w, h in self.regions]

        # Detect QBNO regions
        qbno_responses = [self.detect_shaded_qbno(self.cv_image[y:y+h, x:x+w]) for _, x, y, w, h in self.qbno_regions]
        
        # Ask the user where to save the CSV file
        output_csv = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        
        if output_csv:
            self.save_responses(qpseries_responses, roll_number_responses, qbno_responses, responses, output_csv)
    def save_responses(self, qpseries_responses, roll_number_responses, qbno_responses, responses, output_csv):
        with open(output_csv, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            header = ['ROLLNO', 'QBNO', 'QPSERIES'] + [f'A{i}' for i in range(1, len(self.regions) + 1)] + ['Front side Image']
            writer.writerow(header)

            # Concatenate all roll number responses into a single string without commas
            roll_number_response_str = ''.join(roll_number_responses)
            qbno_response_str = ''.join(qbno_responses)

            row = [roll_number_response_str, qbno_response_str, qpseries_responses] + responses + ['Image_1.jpg']  # Replace with actual logic to get image paths
            writer.writerow(row)

        print(f"Responses saved to {output_csv}")

    def detect_shaded_qbno(self, cropped_image):
        # Apply Gaussian blur to reduce noise
        blurred_image = cv2.GaussianBlur(cropped_image, (9, 9), 0)
        # Perform binary thresholding to detect filled regions (assuming QBNO numbers are filled)
        _, binary_image = cv2.threshold(cropped_image, 25, 255, cv2.THRESH_BINARY_INV)

        # Find contours
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Calculate dimensions and regions for digits 0 to 9 (vertical)
        height, width = cropped_image.shape
        digit_regions = [
            (0, 0, width, height // 10),  # Region for digit 0
            (0, height // 10, width, 2 * height // 10),  # Region for digit 1
            (0, 2 * height // 10, width, 3 * height // 10),  # Region for digit 2
            (0, 3 * height // 10, width, 4 * height // 10),  # Region for digit 3
            (0, 4 * height // 10, width, 5 * height // 10),  # Region for digit 4
            (0, 5 * height // 10, width, 6 * height // 10),  # Region for digit 5
            (0, 6 * height // 10, width, 7 * height // 10),  # Region for digit 6
            (0, 7 * height // 10, width, 8 * height // 10),  # Region for digit 7
            (0, 8 * height // 10, width, 9 * height // 10),  # Region for digit 8
            (0, 9 * height // 10, width, height)  # Region for digit 9
        ]

        # Variables to keep track of detected digits
        detected_digits = []

        # Iterate through each digit region
        for digit, (x1, y1, x2, y2) in enumerate(digit_regions):
            digit_mask = np.zeros_like(binary_image)
            cv2.rectangle(digit_mask, (x1, y1), (x2, y2), 255, -1)  # Create a mask for the current digit region

            # Calculate the intersection of contours with the digit mask
            intersection = cv2.bitwise_and(binary_image, binary_image, mask=digit_mask)

            # Find contours in the intersection area
            digit_contours, _ = cv2.findContours(intersection, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # If there are contours in the digit region, consider it marked
            if digit_contours:
                detected_digits.append(str(digit))  # Add detected digit (0-9) to list

        # Determine the final response based on detected digits
        if len(detected_digits) == 0:
            return 'X'  # No digit marked
     #   elif len(detected_digits) > 1:
     #       return '*'  # Multiple digits marked
        else:
            return detected_digits[0]  # Return the detected digit

    def detect_shaded_option(self, cropped_image):
        # Apply Gaussian blur to reduce noise
        blurred_image = cv2.GaussianBlur(cropped_image, (5, 5), 0)

        # Perform binary thresholding to detect filled bubbles (assuming options are filled)
        _, binary_image = cv2.threshold(blurred_image, 100, 255, cv2.THRESH_BINARY_INV)

        # Find contours
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
        # Calculate dimensions and regions for options A, B, C, D
        height, width = cropped_image.shape
        option_width = width // 4
        option_regions = [
            (0, 0, option_width, height),           # Region for option A
            (option_width, 0, 2*option_width, height), # Region for option B
            (2*option_width, 0, 3*option_width, height), # Region for option C
            (3*option_width, 0, width, height)        # Region for option D
    ]

        # Initialize a list to store detected options
        detected_options = []

        # Iterate over option regions
        for idx, (x1, y1, x2, y2) in enumerate(option_regions):
            option_mask = np.zeros_like(binary_image)
            cv2.rectangle(option_mask, (x1, y1), (x2, y2), 255, -1)

            # Calculate the intersection of contours with the option mask
            intersection = cv2.bitwise_and(binary_image, binary_image, mask=option_mask)

            # Find contours in the intersection area
            option_contours, _ = cv2.findContours(intersection, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Analyze contours to avoid false positives
            for contour in option_contours:
                area = cv2.contourArea(contour)
                if area > 80:  # Adjust area threshold according to your needs
                    detected_options.append(chr(ord('A') + idx))
                    break  # Stop checking contours for this option after detecting one

        # Determine the final response based on detected options
        if len(detected_options) == 0:
            return 'X'  # No option marked
        elif len(detected_options) > 1:
            return '*'  # Multiple options marked
        else:
            return detected_options[0]  # Return the detected option

    def detect_shaded_roll_number(self, cropped_image):
        # Apply Gaussian blur to reduce noise
        blurred_image = cv2.GaussianBlur(cropped_image, (5, 5), 0)
        # Perform binary thresholding to detect filled regions (assuming roll numbers are filled)
        _, binary_image = cv2.threshold(blurred_image, 100, 255, cv2.THRESH_BINARY_INV)

        # Define specific bounding boxes for each bubble
        # You need to adjust these bounding boxes according to your actual bubble positions and sizes
        bubble_regions = [
           (0, 0, cropped_image.shape[1], cropped_image.shape[0] // 10), 
           (0, cropped_image.shape[0] // 10, cropped_image.shape[1], 2 * cropped_image.shape[0] // 10), 
           (0, 2 * cropped_image.shape[0] // 10, cropped_image.shape[1], 3 * cropped_image.shape[0] // 10), 
           (0, 3 * cropped_image.shape[0] // 10, cropped_image.shape[1], 4 * cropped_image.shape[0] // 10), 
           (0, 4 * cropped_image.shape[0] // 10, cropped_image.shape[1], 5 * cropped_image.shape[0] // 10), 
           (0, 5 * cropped_image.shape[0] // 10, cropped_image.shape[1], 6 * cropped_image.shape[0] // 10), 
           (0, 6 * cropped_image.shape[0] // 10, cropped_image.shape[1], 7 * cropped_image.shape[0] // 10), 
           (0, 7 * cropped_image.shape[0] // 10, cropped_image.shape[1], 8 * cropped_image.shape[0] // 10), 
           (0, 8 * cropped_image.shape[0] // 10, cropped_image.shape[1], 9 * cropped_image.shape[0] // 10), 
           (0, 9 * cropped_image.shape[0] // 10, cropped_image.shape[1], cropped_image.shape[0])
    ]

        detected_digits = []

        # Iterate through each bubble region
        for digit, (x1, y1, x2, y2) in enumerate(bubble_regions):
            # Create a mask for the current bubble region
            bubble_mask = np.zeros_like(binary_image)
            cv2.rectangle(bubble_mask, (x1, y1), (x2, y2), 255, -1)
        
            # Calculate the intersection of contours with the bubble mask
            intersection = cv2.bitwise_and(binary_image, binary_image, mask=bubble_mask)
        
            # Find contours in the intersection area
            bubble_contours, _ = cv2.findContours(intersection, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
            # Analyze contours to ensure they are sufficiently large to be considered filled
            if bubble_contours:
                for contour in bubble_contours:
                    area = cv2.contourArea(contour)
                    if area > 100:  # Adjust the area threshold according to your needs
                         detected_digits.append(str(digit))
                         break

        # Determine the final response based on detected digits
        if len(detected_digits) == 0:
            return 'X'  # No digit marked
        elif len(detected_digits) > 1:
            return '*'  # Multiple digits marked
        else:
            return detected_digits[0]  # Return the detected digit
    def detect_shaded_option_qp(self, cropped_image):
        # Perform binary thresholding to detect white bubbles
        _, binary_image = cv2.threshold(cropped_image, 50, 255, cv2.THRESH_BINARY_INV)

        # Find contours
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Calculate dimensions and regions for options A, B, C, D
        height, width = cropped_image.shape
        option_height = height // 4
        option_regions = [
            (0, 0, width, option_height),               # Region for option A
            (0, option_height, width, 2*option_height), # Region for option B
            (0, 2*option_height, width, 3*option_height), # Region for option C
            (0, 3*option_height, width, height)         # Region for option D
        ]

        # Initialize a list to store detected options
        detected_options = []

        # Iterate over option regions
        for idx, (x1, y1, x2, y2) in enumerate(option_regions):
            option_mask = np.zeros_like(binary_image)
            cv2.rectangle(option_mask, (x1, y1), (x2, y2), 255, -1)  # Create a mask for the current option region

            # Calculate the intersection of contours with the option mask
            intersection = cv2.bitwise_and(binary_image, binary_image, mask=option_mask)

            # Find contours in the intersection area
            option_contours, _ = cv2.findContours(intersection, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # If there are contours in the option region, consider it marked
            if option_contours:
                detected_options.append(chr(65 + idx))  # ('A', 'B', 'C', 'D')

        # Determine the final response based on detected options
        if len(detected_options) == 0:
            return 'X'  # No option marked
        elif len(detected_options) > 1:
            return '*'  # Multiple options marked
        else:
            return detected_options[0]  # Single option marked

    def save_template(self):
        template_file = filedialog.asksaveasfilename(defaultextension=".gs", filetypes=[("template files", "*.gs")])
        if template_file:
            with open(template_file, 'w') as file:
                json.dump({'qpseries_region': self.qpseries_region, 'question_regions': self.regions, 'roll_number_regions': self.roll_number_regions, 'qbno_regions': self.qbno_regions}, file)
            print(f"Template saved to {template_file}")

    def load_template(self):
        template_file = filedialog.askopenfilename(filetypes=[("template files", "*.gs")])
        if template_file:
            with open(template_file, 'r') as file:
                template_data = json.load(file)
                self.qpseries_region = template_data.get('qpseries_region', None)
                self.regions = template_data.get('question_regions', [])
                self.roll_number_regions = template_data.get('roll_number_regions', [])
                self.qbno_regions = template_data.get('qbno_regions', [])
            print(f"Template loaded from {template_file}")

    def scan_multiple_images(self):
        threading.Thread(target=self._scan_multiple_images_thread).start()

    def _scan_multiple_images_thread(self):
        self.load_template()
        image_folder = filedialog.askdirectory(title="Select Folder with OMR Images")
        if not image_folder:
            print("No folder selected.")
            return

        # Check for the presence of the dummy text file
        dummy_file_path = os.path.join(image_folder, "alignment_done.txt")
        if not os.path.exists(dummy_file_path):
            proceed = messagebox.askyesno("Alignment Check", "Images may not be aligned. Do you want to proceed with scanning?")
            if not proceed:
                return

        output_csv = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not output_csv:
            print("No output file selected.")
            return

        self.loading_label.config(text="Scanning images, please wait...")
        self.loading_label.pack(pady=10)  # Show loading label

        self.root.update_idletasks()  # Update the GUI to show the loading message

        responses = []
        image_paths = []

        total_images = len([file for file in os.listdir(image_folder) if file.lower().endswith(('f.jpg'))])
        processed_count = 0

        # List to store CSV rows
        csv_data = []

        for image_file in os.listdir(image_folder):
            if image_file.lower().endswith('f.jpg'):
                image_path = os.path.join(image_folder, image_file)
                image_paths.append(image_path)
                cv_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

                # Detect QPSERIES response
                qpseries_response = self.detect_shaded_option_qp(cv_image[self.qpseries_region[1]:self.qpseries_region[3], self.qpseries_region[0]:self.qpseries_region[2]])

                # Detect roll number responses
                roll_number_responses = [self.detect_shaded_roll_number(cv_image[y:y+h, x:x+w]) for _, x, y, w, h in self.roll_number_regions]

                # Detect question responses
                question_responses = [self.detect_shaded_option(cv_image[y:y+h, x:x+w]) for _, x, y, w, h in self.regions]

                # Detect QBNO regions
                qbno_responses = [self.detect_shaded_qbno(cv_image[y:y+h, x:x+w]) for _, x, y, w, h in self.qbno_regions]

                responses.append((qpseries_response, roll_number_responses, question_responses, qbno_responses))
                processed_count += 1

                # Update progress label or print to console
                self.loading_label.config(text=f"Scanning image {processed_count} of {total_images}...")

                # Append row to csv_data list
                roll_number_response_str = ''.join(roll_number_responses)
                qbno_response_str = ''.join(qbno_responses)
                row = [roll_number_response_str, qbno_response_str, qpseries_response] + question_responses + [image_paths[-1]]  # Using -1 to get the last added image path
                csv_data.append(row)

                # Update GUI or print to console with current data
                current_data_str = f"Current Data:\nROLLNO: {roll_number_response_str}\nQBNO: {qbno_response_str}\nQPSERIES: {qpseries_response}\nQuestions: {question_responses}\nImage Path: {image_paths[-1]}\n\n"
                print(current_data_str)  # Print to console

        # Write accumulated data to CSV file
        with open(output_csv, 'w', newline='') as csvfile:
           writer = csv.writer(csvfile)
           header = ['ROLLNO', 'QBNO', 'QPSERIES'] + [f'A{i}' for i in range(1, len(self.regions) + 1)] + ['Front side Image']
           writer.writerow(header)

           for row in csv_data:
               writer.writerow(row)

        print(f"Responses saved to {output_csv}")
        messagebox.showinfo("CSV Saved", f"Responses saved to {output_csv}\nTotal count: {processed_count}")

        # Prompt user to view CSV file
        view_csv = messagebox.askyesno("View CSV File", "Do you want to view the CSV file now?")
        if view_csv:
            try:
                os.startfile(output_csv)  # Opens the CSV file with the default application
            except Exception as e:
                print(f"Failed to open file: {e}")
        self.loading_label.pack_forget()  # Remove loading label after scanning

        # Show success message
        messagebox.showinfo("Success", "Images extracted successfully.")

    def align_images(self, template_path, image_path, max_features=10000, good_match_percent=100):
        # Load template and image to align
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        
        if template is None or image is None:
            messagebox.showerror("Error", f"Failed to load image or template: {image_path}")
            return False
        
        # Detect ORB features and compute descriptors.
        orb = cv2.ORB_create(max_features)
        keypoints1, descriptors1 = orb.detectAndCompute(template, None)
        keypoints2, descriptors2 = orb.detectAndCompute(image, None)
        
        # Match features using a brute-force matcher
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = matcher.match(descriptors1, descriptors2)
        
       
        # Sort matches by score
        matches = sorted(matches, key=lambda x: x.distance)
        
        # Adjust good match selection based on the number of matches
        num_good_matches = min(len(matches), max(1, int(len(matches) * good_match_percent)))
        matches = matches[:num_good_matches]
        
        # Extract points for homography calculation
        points1 = np.float32([keypoints1[match.queryIdx].pt for match in matches]).reshape(-1, 1, 2)
        points2 = np.float32([keypoints2[match.trainIdx].pt for match in matches]).reshape(-1, 1, 2)
        
        # Find homography using RANSAC
        h, _ = cv2.findHomography(points2, points1, cv2.RANSAC, 5.0)
        
        # Use homography to warp image
        height, width = template.shape
        aligned_image = cv2.warpPerspective(image, h, (width, height))
        
        # Save aligned image back to original image path
        cv2.imwrite(image_path, aligned_image)
        
       # print(f"Alignment complete. Aligned image saved at {image_path}")
        return True

    def upload_template(self):
        template_path = filedialog.askopenfilename(title="Select Template Image", filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")])
        if template_path:
            self.template_entry.delete(0, tk.END)
            self.template_entry.insert(0, template_path)

    def select_image_directory(self):
        image_dir = filedialog.askdirectory(title="Select Directory with Images to Align")
        if image_dir:
            self.image_dir_entry.delete(0, tk.END)
            self.image_dir_entry.insert(0, image_dir)

    def align_images_in_directory(self):
      template_path = self.template_entry.get()
      image_dir = self.image_dir_entry.get()

      if not template_path or not image_dir:
          messagebox.showwarning("Input Error", "Please select all required directories.")
          return

      try:
         # Show loading label for alignment process
         self.loading_label.config(text="Aligning images, please wait...")
         self.loading_label.pack(pady=10)
         self.root.update_idletasks()

         # Prepare a list of image files to process
         image_files = [f for f in os.listdir(image_dir) if f.lower().endswith('f.jpg')]

         # Create a tqdm progress bar
         with tqdm(total=len(image_files), desc="Aligning images", unit="file") as pbar:
             aligned_count = 0  # Counter for aligned images

             for image_file in image_files:
                 image_path = os.path.join(image_dir, image_file)
                 try:
                    self.align_images(template_path, image_path)
                    aligned_count += 1
                 except Exception as e:
                    print(f"Error aligning {image_path}: {str(e)}")

                 # Update the progress bar
                 pbar.update(1)
                
                 # Update the GUI label with the progress
                 self.loading_label.config(text=f"Aligning images: {aligned_count}/{len(image_files)} done...")
                 self.root.update_idletasks()

         # Create dummy file after alignment
         dummy_file_path = os.path.join(image_dir, 'alignment_done.txt')
         with open(dummy_file_path, 'w') as dummy_file:
             dummy_file.write("Alignment complete.")

         messagebox.showinfo("Success", f"Aligned {aligned_count} 'F.jpg' images saved in {image_dir}")
      finally:
         self.loading_label.pack_forget()  # Remove loading label after alignment


    

if __name__ == "__main__":
    root = tk.Tk()
    app = OMRApp(root)
    root.mainloop()
