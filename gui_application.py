import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import threading

# Import our ASCII generator and image processor
from ascii_art_generator import ASCIIArtGenerator
from image_processor import ImageProcessor

class ASCIIArtApp(tk.Tk):
    """
    GUI application for the ASCII Art Generator.

    Provides a user-friendly interface for:
    - Loading and displaying images
    - Customizing ASCII conversion parameters
    - Previewing results
    - Saving ASCII art to file
    """

    def __init__(self):
        """Initialize the application."""
        super().__init__()

        self.title("ASCII Art Generator")
        self.geometry("1200x800")
        self.minsize(800, 600)

        # Internal state
        self.input_image_path = None
        self.output_path = None
        self.ascii_result = None
        self.processor = ImageProcessor()
        self.current_preview = None

        # Set up the UI
        self._create_menu()
        self._create_main_layout()
        self._setup_bindings()

        # Set up default values
        self._set_default_values()

        # Configure style
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6)
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0")

        # Status message
        self.status_var = tk.StringVar()
        self.status_var.set("Ready. Load an image to begin.")
        self.status_bar = ttk.Label(self, textvariable=self.status_var,
                                   relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_menu(self):
        """Create the application menu."""
        menubar = tk.Menu(self)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open Image", command=self._load_image)
        file_menu.add_command(label="Save ASCII Art", command=self._save_ascii_art)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Instructions", command=self._show_instructions)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def _create_main_layout(self):
        """Create the main application layout."""
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Split into left (settings) and right (preview) sides
        settings_frame = ttk.LabelFrame(main_frame, text="Settings")
        settings_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)

        preview_frame = ttk.LabelFrame(main_frame, text="Preview")
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create settings widgets
        self._create_settings_panel(settings_frame)

        # Create preview panel
        self._create_preview_panel(preview_frame)

    def _create_settings_panel(self, parent):
        """Create the settings panel with all controls."""
        # File selection
        file_frame = ttk.Frame(parent)
        file_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(file_frame, text="Image:").pack(side=tk.LEFT, padx=5)
        self.file_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Browse...", command=self._load_image).pack(side=tk.LEFT, padx=5)

        # Create a notebook for categorizing settings
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ASCII settings tab
        ascii_frame = ttk.Frame(notebook)
        notebook.add(ascii_frame, text="ASCII Settings")

        # Image processing tab
        img_frame = ttk.Frame(notebook)
        notebook.add(img_frame, text="Image Processing")

        # Advanced tab
        adv_frame = ttk.Frame(notebook)
        notebook.add(adv_frame, text="Advanced")

        # Populate ASCII settings tab
        self._create_ascii_settings(ascii_frame)

        # Populate image processing tab
        self._create_image_processing(img_frame)

        # Populate advanced tab
        self._create_advanced_settings(adv_frame)

        # Action buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=5, pady=10)

        ttk.Button(btn_frame, text="Generate Preview", command=self._generate_preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Generate Full", command=self._generate_full).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Save As...", command=self._save_ascii_art).pack(side=tk.RIGHT, padx=5)

    def _create_ascii_settings(self, parent):
        """Create controls for basic ASCII conversion settings."""
        # Width setting
        width_frame = ttk.Frame(parent)
        width_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(width_frame, text="Width:").pack(side=tk.LEFT, padx=5)
        self.width_var = tk.IntVar()
        ttk.Spinbox(width_frame, from_=20, to=500, textvariable=self.width_var, width=5).pack(side=tk.LEFT, padx=5)

        # Height setting
        height_frame = ttk.Frame(parent)
        height_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(height_frame, text="Height:").pack(side=tk.LEFT, padx=5)
        self.height_var = tk.IntVar()
        self.height_spinbox = ttk.Spinbox(height_frame, from_=0, to=500, textvariable=self.height_var, width=5)
        self.height_spinbox.pack(side=tk.LEFT, padx=5)

        self.auto_height_var = tk.BooleanVar()
        ttk.Checkbutton(height_frame, text="Auto (maintain aspect ratio)",
                      variable=self.auto_height_var,
                      command=self._toggle_height_auto).pack(side=tk.LEFT, padx=5)

        # Character set selection
        char_frame = ttk.Frame(parent)
        char_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(char_frame, text="Character Set:").pack(side=tk.LEFT, padx=5)
        self.char_set_var = tk.StringVar()
        char_combo = ttk.Combobox(char_frame, textvariable=self.char_set_var, width=15)
        char_combo['values'] = ('basic', 'standard', 'blocks', 'custom')
        char_combo.pack(side=tk.LEFT, padx=5)

        # Invert option
        invert_frame = ttk.Frame(parent)
        invert_frame.pack(fill=tk.X, padx=5, pady=5)

        self.invert_var = tk.BooleanVar()
        ttk.Checkbutton(invert_frame, text="Invert Colors",
                      variable=self.invert_var).pack(side=tk.LEFT, padx=5)

        self.dither_var = tk.BooleanVar()
        ttk.Checkbutton(invert_frame, text="Apply Dithering",
                      variable=self.dither_var).pack(side=tk.LEFT, padx=20)

    def _create_image_processing(self, parent):
        """Create controls for image preprocessing settings."""
        # Contrast adjustment
        contrast_frame = ttk.Frame(parent)
        contrast_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(contrast_frame, text="Contrast:").pack(side=tk.LEFT, padx=5)
        self.contrast_var = tk.DoubleVar()
        ttk.Scale(contrast_frame, from_=0.1, to=3.0, variable=self.contrast_var,
                orient=tk.HORIZONTAL, length=200).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Label(contrast_frame, textvariable=self.contrast_var).pack(side=tk.LEFT, padx=5)

        # Brightness adjustment
        brightness_frame = ttk.Frame(parent)
        brightness_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(brightness_frame, text="Brightness:").pack(side=tk.LEFT, padx=5)
        self.brightness_var = tk.DoubleVar()
        ttk.Scale(brightness_frame, from_=0.1, to=3.0, variable=self.brightness_var,
                orient=tk.HORIZONTAL, length=200).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Label(brightness_frame, textvariable=self.brightness_var).pack(side=tk.LEFT, padx=5)

        # Sharpness adjustment
        sharpness_frame = ttk.Frame(parent)
        sharpness_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(sharpness_frame, text="Sharpness:").pack(side=tk.LEFT, padx=5)
        self.sharpness_var = tk.DoubleVar()
        ttk.Scale(sharpness_frame, from_=0.1, to=5.0, variable=self.sharpness_var,
                orient=tk.HORIZONTAL, length=200).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Label(sharpness_frame, textvariable=self.sharpness_var).pack(side=tk.LEFT, padx=5)

        # Edge enhancement
        edge_frame = ttk.Frame(parent)
        edge_frame.pack(fill=tk.X, padx=5, pady=5)

        self.enhance_edges_var = tk.BooleanVar()
        ttk.Checkbutton(edge_frame, text="Enhance Edges",
                      variable=self.enhance_edges_var).pack(side=tk.LEFT, padx=5)

        self.edge_mode_var = tk.StringVar()
        edge_combo = ttk.Combobox(edge_frame, textvariable=self.edge_mode_var, width=10, state="readonly")
        edge_combo['values'] = ('standard', 'sobel', 'canny')
        edge_combo.pack(side=tk.LEFT, padx=5)

        # Histogram equalization
        hist_frame = ttk.Frame(parent)
        hist_frame.pack(fill=tk.X, padx=5, pady=5)

        self.hist_equal_var = tk.BooleanVar()
        ttk.Checkbutton(hist_frame, text="Apply Histogram Equalization",
                      variable=self.hist_equal_var).pack(side=tk.LEFT, padx=5)

        # Unsharp mask
        unsharp_frame = ttk.Frame(parent)
        unsharp_frame.pack(fill=tk.X, padx=5, pady=5)

        self.unsharp_mask_var = tk.BooleanVar()
        ttk.Checkbutton(unsharp_frame, text="Apply Unsharp Mask",
                      variable=self.unsharp_mask_var).pack(side=tk.LEFT, padx=5)

        # Radius and amount for unsharp mask
        self.unsharp_radius_var = tk.DoubleVar()
        self.unsharp_amount_var = tk.DoubleVar()

        unsharp_params_frame = ttk.Frame(parent)
        unsharp_params_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(unsharp_params_frame, text="Radius:").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(unsharp_params_frame, from_=0.5, to=5.0, increment=0.5,
                   textvariable=self.unsharp_radius_var, width=5).pack(side=tk.LEFT, padx=5)

        ttk.Label(unsharp_params_frame, text="Amount:").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(unsharp_params_frame, from_=0.5, to=3.0, increment=0.1,
                   textvariable=self.unsharp_amount_var, width=5).pack(side=tk.LEFT, padx=5)

    def _create_advanced_settings(self, parent):
        """Create controls for advanced settings."""
        # Font selection for display
        font_frame = ttk.Frame(parent)
        font_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(font_frame, text="Preview Font:").pack(side=tk.LEFT, padx=5)
        self.font_size_var = tk.IntVar()
        ttk.Spinbox(font_frame, from_=4, to=24, textvariable=self.font_size_var, width=5).pack(side=tk.LEFT, padx=5)

        # Output format options
        format_frame = ttk.Frame(parent)
        format_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(format_frame, text="Output Format:").pack(side=tk.LEFT, padx=5)
        self.output_format_var = tk.StringVar()
        format_combo = ttk.Combobox(format_frame, textvariable=self.output_format_var, width=10, state="readonly")
        format_combo['values'] = ('Text', 'HTML', 'Image')
        format_combo.pack(side=tk.LEFT, padx=5)

        # Custom character set input
        custom_frame = ttk.Frame(parent)
        custom_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(custom_frame, text="Custom Characters:").pack(anchor=tk.W, padx=5, pady=2)
        self.custom_chars_var = tk.StringVar()
        ttk.Entry(custom_frame, textvariable=self.custom_chars_var, width=40).pack(padx=5, pady=2, fill=tk.X)
        ttk.Label(custom_frame, text="(From darkest to lightest)").pack(anchor=tk.W, padx=5, pady=2)

        # Adaptive thresholding
        thresh_frame = ttk.Frame(parent)
        thresh_frame.pack(fill=tk.X, padx=5, pady=5)

        self.adaptive_thresh_var = tk.BooleanVar()
        ttk.Checkbutton(thresh_frame, text="Apply Adaptive Thresholding",
                       variable=self.adaptive_thresh_var).pack(side=tk.LEFT, padx=5)

        # Threshold parameters
        thresh_params_frame = ttk.Frame(parent)
        thresh_params_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(thresh_params_frame, text="Block Size:").pack(side=tk.LEFT, padx=5)
        self.thresh_block_var = tk.IntVar()
        block_spin = ttk.Spinbox(thresh_params_frame, from_=3, to=51, increment=2,
                               textvariable=self.thresh_block_var, width=5)
        block_spin.pack(side=tk.LEFT, padx=5)

        ttk.Label(thresh_params_frame, text="Constant:").pack(side=tk.LEFT, padx=5)
        self.thresh_c_var = tk.IntVar()
        ttk.Spinbox(thresh_params_frame, from_=0, to=10,
                   textvariable=self.thresh_c_var, width=5).pack(side=tk.LEFT, padx=5)

        # Reset to defaults button
        reset_frame = ttk.Frame(parent)
        reset_frame.pack(fill=tk.X, padx=5, pady=10)

        ttk.Button(reset_frame, text="Reset to Defaults",
                  command=self._set_default_values).pack(side=tk.RIGHT, padx=5)

    def _create_preview_panel(self, parent):
        """Create the preview panel with tabs for original image and ASCII result."""
        # Create notebook with tabs for original and ASCII
        self.preview_notebook = ttk.Notebook(parent)
        self.preview_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Original image tab
        self.original_frame = ttk.Frame(self.preview_notebook)
        self.preview_notebook.add(self.original_frame, text="Original Image")

        # ASCII result tab
        self.ascii_frame = ttk.Frame(self.preview_notebook)
        self.preview_notebook.add(self.ascii_frame, text="ASCII Result")

        # Image display in original tab
        self.image_canvas = tk.Canvas(self.original_frame, bg="white")
        self.image_canvas.pack(fill=tk.BOTH, expand=True)

        # ASCII display in result tab (scrollable text widget)
        self.ascii_text = scrolledtext.ScrolledText(self.ascii_frame, wrap=tk.NONE)
        self.ascii_text.pack(fill=tk.BOTH, expand=True)

        # Configure default font for ASCII display
        self.ascii_text.config(font=('Courier', 10))

    def _setup_bindings(self):
        """Set up event bindings."""
        # Update height when width changes if auto-height is on
        self.width_var.trace_add("write", self._update_auto_height)

        # Enable/disable edge mode combobox based on edge enhancement checkbox
        self.enhance_edges_var.trace_add("write", self._toggle_edge_mode)

        # Update custom characters when char set changes
        self.char_set_var.trace_add("write", self._update_custom_chars)

        # Enable/disable unsharp mask parameters
        self.unsharp_mask_var.trace_add("write", self._toggle_unsharp_params)

        # Enable/disable threshold parameters
        self.adaptive_thresh_var.trace_add("write", self._toggle_thresh_params)

    def _set_default_values(self):
        """Set default values for all settings."""
        # ASCII settings
        self.width_var.set(100)
        self.height_var.set(50)
        self.auto_height_var.set(True)
        self._toggle_height_auto()

        self.char_set_var.set("standard")
        self.invert_var.set(False)
        self.dither_var.set(False)

        # Image processing
        self.contrast_var.set(1.0)
        self.brightness_var.set(1.0)
        self.sharpness_var.set(1.0)

        self.enhance_edges_var.set(False)
        self.edge_mode_var.set("standard")
        self._toggle_edge_mode()

        self.hist_equal_var.set(False)

        self.unsharp_mask_var.set(False)
        self.unsharp_radius_var.set(2.0)
        self.unsharp_amount_var.set(1.5)
        self._toggle_unsharp_params()

        # Advanced settings
        self.font_size_var.set(10)
        self.output_format_var.set("Text")
        self.custom_chars_var.set(" .`^\",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$")
        self.adaptive_thresh_var.set(False)
        self.thresh_block_var.set(11)
        self.thresh_c_var.set(2)
        self._toggle_thresh_params()

    def _toggle_height_auto(self, *args):
        """Enable/disable height input based on auto-height checkbox."""
        if self.auto_height_var.get():
            self.height_spinbox.configure(state="disabled")
            self._update_auto_height()
        else:
            self.height_spinbox.configure(state="normal")

    def _toggle_edge_mode(self, *args):
        """Enable/disable edge mode combobox based on edge enhancement checkbox."""
        # Find the edge mode combobox and update its state
        for child in self.winfo_children():
            if isinstance(child, ttk.Frame):
                for frame in child.winfo_children():
                    if isinstance(frame, ttk.LabelFrame):
                        for notebook in frame.winfo_children():
                            if isinstance(notebook, ttk.Notebook):
                                for tab in notebook.winfo_children():
                                    for subframe in tab.winfo_children():
                                        for widget in subframe.winfo_children():
                                            if isinstance(widget, ttk.Combobox) and widget.cget("values") == ('standard', 'sobel', 'canny'):
                                                if self.enhance_edges_var.get():
                                                    widget.configure(state="readonly")
                                                else:
                                                    widget.configure(state="disabled")
                                                return

    def _toggle_unsharp_params(self, *args):
        """Enable/disable unsharp mask parameters based on checkbox."""
        state = "normal" if self.unsharp_mask_var.get() else "disabled"

        # Find and update spinboxes for unsharp mask parameters
        for child in self.winfo_children():
            if isinstance(child, ttk.Frame):
                for frame in child.winfo_children():
                    if isinstance(frame, ttk.LabelFrame):
                        for notebook in frame.winfo_children():
                            if isinstance(notebook, ttk.Notebook):
                                for tab in notebook.winfo_children():
                                    for subframe in tab.winfo_children():
                                        if not hasattr(subframe, 'winfo_children'):
                                            continue
                                        for widget in subframe.winfo_children():
                                            if isinstance(widget, ttk.Spinbox) and (
                                                widget.cget("from") == 0.5 and widget.cget("to") == 5.0 or
                                                widget.cget("from") == 0.5 and widget.cget("to") == 3.0
                                            ):
                                                widget.configure(state=state)

    def _toggle_thresh_params(self, *args):
        """Enable/disable threshold parameters based on checkbox."""
        state = "normal" if self.adaptive_thresh_var.get() else "disabled"

        # Find and update spinboxes for threshold parameters
        for child in self.winfo_children():
            if isinstance(child, ttk.Frame):
                for frame in child.winfo_children():
                    if isinstance(frame, ttk.LabelFrame):
                        for notebook in frame.winfo_children():
                            if isinstance(notebook, ttk.Notebook):
                                for tab in notebook.winfo_children():
                                    for subframe in tab.winfo_children():
                                        if not hasattr(subframe, 'winfo_children'):
                                            continue
                                        for widget in subframe.winfo_children():
                                            if isinstance(widget, ttk.Spinbox) and (
                                                widget.cget("from") == 3 and widget.cget("to") == 51 or
                                                widget.cget("from") == 0 and widget.cget("to") == 10
                                            ):
                                                widget.configure(state=state)

    def _update_custom_chars(self, *args):
        """Update custom characters field when char set changes."""
        if self.char_set_var.get() != "custom":
            try:
                # Update custom chars field with the selected character set
                char_set = ASCIIArtGenerator.CHAR_SETS.get(self.char_set_var.get())
                if char_set:
                    self.custom_chars_var.set(char_set)
            except Exception as e:
                print(f"Error updating custom chars: {e}")

    def _update_auto_height(self, *args):
        """Update height based on width and aspect ratio if auto-height is enabled."""
        if hasattr(self, 'auto_height_var') and self.auto_height_var.get():
            if self.input_image_path and os.path.exists(self.input_image_path):
                try:
                    with Image.open(self.input_image_path) as img:
                        # Calculate height to maintain aspect ratio
                        aspect_ratio = img.height / img.width
                        # Multiply by 0.5 to account for character height/width ratio
                        height = int(self.width_var.get() * aspect_ratio * 0.5)
                        self.height_var.set(height)
                except Exception as e:
                    print(f"Error calculating auto height: {e}")

    def _load_image(self):
        """Load an image from file."""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            try:
                # Store image path
                self.input_image_path = file_path
                self.file_path_var.set(file_path)

                # Display image
                self._display_original_image(file_path)

                # Update auto height
                self._update_auto_height()

                # Update status
                self.status_var.set(f"Image loaded: {os.path.basename(file_path)}")

                # Switch to original image tab
                self.preview_notebook.select(0)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}")
                self.status_var.set("Error loading image.")

    def _save_ascii_art(self):
        """Save generated ASCII art to file."""
        if not self.ascii_result:
            messagebox.showwarning("Warning", "No ASCII art has been generated yet.")
            return

        output_format = self.output_format_var.get()

        if output_format == "Text":
            file_path = filedialog.asksaveasfilename(
                title="Save ASCII Art",
                defaultextension=".txt",
                filetypes=[
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ]
            )

            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(self.ascii_result)
                    self.status_var.set(f"ASCII art saved to: {os.path.basename(file_path)}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save file: {e}")

        elif output_format == "HTML":
            file_path = filedialog.asksaveasfilename(
                title="Save ASCII Art as HTML",
                defaultextension=".html",
                filetypes=[
                    ("HTML files", "*.html"),
                    ("All files", "*.*")
                ]
            )

            if file_path:
                try:
                    # Create a simple HTML document with monospace font
                    html_content = f"""<!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <title>ASCII Art</title>
                        <style>
                            pre {{
                                font-family: monospace;
                                font-size: 10px;
                                line-height: 1.0;
                                white-space: pre;
                            }}
                        </style>
                    </head>
                    <body>
                        <pre>{self.ascii_result}</pre>
                    </body>
                    </html>"""

                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    self.status_var.set(f"ASCII art saved as HTML to: {os.path.basename(file_path)}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save HTML file: {e}")

        elif output_format == "Image":
            file_path = filedialog.asksaveasfilename(
                title="Save ASCII Art as Image",
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("JPEG files", "*.jpg"),
                    ("All files", "*.*")
                ]
            )

            if file_path:
                try:
                    # Save the content of the text widget as an image
                    # This is a simplified version - a more robust solution would
                    # render the ASCII art to an image with proper spacing
                    self.ascii_text.update()
                    x = self.ascii_text.winfo_rootx()
                    y = self.ascii_text.winfo_rooty()
                    width = self.ascii_text.winfo_width()
                    height = self.ascii_text.winfo_height()

                    # Take a screenshot of the text widget
                    img = ImageTk.PhotoImage(Image.grab((x, y, x+width, y+height)))
                    img._image.save(file_path)

                    self.status_var.set(f"ASCII art saved as image to: {os.path.basename(file_path)}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save image: {e}")

    def _generate_preview(self):
        """Generate a preview of the ASCII art with reduced settings."""
        if not self.input_image_path:
            messagebox.showwarning("Warning", "No image loaded. Please load an image first.")
            return

        # Use smaller dimensions for preview
        preview_width = min(80, self.width_var.get())

        # Calculate preview height
        if self.auto_height_var.get():
            with Image.open(self.input_image_path) as img:
                aspect_ratio = img.height / img.width
                preview_height = int(preview_width * aspect_ratio * 0.5)
        else:
            preview_height = min(40, self.height_var.get())

        try:
            # Show busy cursor
            self.config(cursor="wait")
            self.update()

            # Generate the ASCII art
            self._generate_ascii_art(preview_width, preview_height)

            # Switch to ASCII result tab
            self.preview_notebook.select(1)

            # Update status
            self.status_var.set(f"Preview generated ({preview_width}x{preview_height} characters).")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate preview: {e}")
            self.status_var.set("Error generating preview.")
        finally:
            # Restore cursor
            self.config(cursor="")

    def _generate_full(self):
        """Generate full ASCII art with all settings."""
        if not self.input_image_path:
            messagebox.showwarning("Warning", "No image loaded. Please load an image first.")
            return

        try:
            # Show busy cursor
            self.config(cursor="wait")
            self.update()

            # Start a thread for generation to keep UI responsive
            threading.Thread(target=self._threaded_generation, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start generation: {e}")
            self.status_var.set("Error starting generation.")
            self.config(cursor="")

    def _display_original_image(self, file_path):
        """Display the original image in the canvas."""
        try:
            # Clear previous image
            self.image_canvas.delete("all")

            # Open and resize image to fit canvas
            image = Image.open(file_path)
            self.image_canvas.update()  # Update to get current dimensions

            # Calculate scaling to fit canvas while maintaining aspect ratio
            canvas_width = self.image_canvas.winfo_width()
            canvas_height = self.image_canvas.winfo_height()

            img_width, img_height = image.size

            # Calculate scale factor to fit within canvas
            scale_width = canvas_width / img_width if img_width > canvas_width else 1
            scale_height = canvas_height / img_height if img_height > canvas_height else 1
            scale = min(scale_width, scale_height)

            # Resize image
            if scale < 1:
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                image = image.resize((new_width, new_height), Image.LANCZOS)

            # Convert to PhotoImage for display
            self.current_preview = ImageTk.PhotoImage(image)

            # Add to canvas
            self.image_canvas.create_image(
                canvas_width // 2, canvas_height // 2,
                image=self.current_preview,
                anchor=tk.CENTER
            )

        except Exception as e:
            print(f"Error displaying image: {e}")
            self.image_canvas.create_text(
                self.image_canvas.winfo_width() // 2,
                self.image_canvas.winfo_height() // 2,
                text=f"Error displaying image: {e}",
                fill="red"
            )

    def _threaded_generation(self):
        """Generate ASCII art in a separate thread to keep UI responsive."""
        try:
            # Get current settings
            width = self.width_var.get()
            height = None if self.auto_height_var.get() else self.height_var.get()

            # Generate ASCII art
            self._generate_ascii_art(width, height)

            # Update UI on main thread
            self.after(0, self._update_ui_after_generation)

        except Exception as e:
            # Update UI on main thread
            self.after(0, lambda: self._show_generation_error(str(e)))

    def _update_ui_after_generation(self):
        """Update UI after successful generation."""
        # Switch to ASCII result tab
        self.preview_notebook.select(1)

        # Update status
        self.status_var.set(f"ASCII art generated successfully.")

        # Restore cursor
        self.config(cursor="")

    def _show_generation_error(self, error_msg):
        """Show error message after failed generation."""
        messagebox.showerror("Generation Error", f"Failed to generate ASCII art: {error_msg}")
        self.status_var.set("Error generating ASCII art.")
        self.config(cursor="")

    def _generate_ascii_art(self, width, height):
        """Generate ASCII art with the specified dimensions."""
        if not self.input_image_path:
            raise ValueError("No image loaded")

        # Process image first with ImageProcessor
        self.processor = ImageProcessor()
        self.processor.load(self.input_image_path)

        # Apply image processing based on settings
        self.processor.resize(width, height)

        if self.sharpness_var.get() != 1.0:
            self.processor.adjust_sharpness(self.sharpness_var.get())

        if self.contrast_var.get() != 1.0:
            self.processor.adjust_contrast(self.contrast_var.get())

        if self.brightness_var.get() != 1.0:
            self.processor.adjust_brightness(self.brightness_var.get())

        if self.hist_equal_var.get():
            self.processor.apply_histogram_equalization()

        if self.enhance_edges_var.get():
            self.processor.detect_edges(self.edge_mode_var.get())

        if self.unsharp_mask_var.get():
            self.processor.apply_unsharp_mask(
                radius=self.unsharp_radius_var.get(),
                amount=self.unsharp_amount_var.get()
            )

        if self.adaptive_thresh_var.get():
            self.processor.apply_adaptive_thresholding(
                block_size=self.thresh_block_var.get(),
                c=self.thresh_c_var.get()
            )

        # Get processed image
        processed_img = self.processor.get_processed_image()

        # Create ASCII generator
        char_set = self.char_set_var.get()

        # If custom is selected, use the custom chars
        if char_set == "custom":
            ASCIIArtGenerator.CHAR_SETS['custom'] = self.custom_chars_var.get()

        generator = ASCIIArtGenerator(
            char_set=char_set,
            width=width,
            height=height,
            contrast=1.0,  # Already applied in image processing
            brightness=1.0,  # Already applied in image processing
            invert=self.invert_var.get(),
            dither=self.dither_var.get()
        )

        # Generate ASCII from the processed image
        ascii_art = generator._map_pixels_to_ascii(processed_img)

        # Join characters into string
        result = '\n'.join([''.join(row) for row in ascii_art])

        # Store and display result
        self.ascii_result = result

        # Update text widget with result
        self.ascii_text.config(state=tk.NORMAL)
        self.ascii_text.delete(1.0, tk.END)
        self.ascii_text.insert(1.0, result)
        self.ascii_text.config(state=tk.DISABLED)

        # Update font size
        self.ascii_text.config(font=('Courier', self.font_size_var.get()))

    def _show_instructions(self):
        """Show application instructions."""
        instructions = """
    ASCII Art Generator - Instructions

    1. Getting Started:
       - Click 'File > Open Image' or the 'Browse...' button to load an image
       - Adjust settings in the different tabs
       - Click 'Generate Preview' to quickly see a low-resolution result
       - Click 'Generate Full' for the complete ASCII art

    2. ASCII Settings:
       - Width/Height: Number of characters in the output
       - Character Set: Different character collections for varied results
       - Invert Colors: Reverse dark and light values
       - Apply Dithering: Add texture to improve detail perception

    3. Image Processing:
       - Contrast/Brightness/Sharpness: Adjust image properties
       - Enhance Edges: Highlight edges with different algorithms
       - Histogram Equalization: Improve contrast across the entire range
       - Unsharp Mask: Enhance edges while preserving overall appearance

    4. Advanced Settings:
       - Preview Font: Change display font size
       - Output Format: Save as text, HTML, or image
       - Custom Characters: Define your own density map
       - Adaptive Thresholding: Better detail in varied lighting

    5. Tips:
       - For best results, use high-contrast images
       - Experiment with different character sets
       - Adjust width based on where you'll display the result
       - Small changes in contrast can dramatically improve results
        """

        # Show in a new dialog window
        dialog = tk.Toplevel(self)
        dialog.title("Instructions")
        dialog.geometry("600x500")
        dialog.transient(self)
        dialog.grab_set()

        text = scrolledtext.ScrolledText(dialog, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(1.0, instructions)
        text.config(state=tk.DISABLED)

        btn = ttk.Button(dialog, text="Close", command=dialog.destroy)
        btn.pack(pady=10)

    def _show_about(self):
        """Show about dialog."""
        about_text = """
    ASCII Art Generator v1.0

    A powerful tool for converting images to ASCII art with extensive customization options.

    Features:
    - Multiple character sets and image processing options
    - Preview and full generation modes
    - Save as text, HTML, or image
    - Advanced image processing capabilities

    Created using Python, Tkinter, PIL, and OpenCV.
        """

        messagebox.showinfo("About ASCII Art Generator", about_text)


if __name__ == "__main__":
    app = ASCIIArtApp()
    app.mainloop()
