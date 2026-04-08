"""
ASCII Art Generator - Example Usage Patterns

This script demonstrates various ways to use the ASCII Art Generator
library programmatically for different use cases.
"""

import os
import sys
from PIL import Image
from ascii_art_generator import ASCIIArtGenerator
from image_processor import ImageProcessor

def basic_usage(input_image):
    """Basic usage with default settings."""
    print("\n=== Basic Usage ===\n")
    
    # Create generator with default settings
    generator = ASCIIArtGenerator(width=80)
    
    # Convert image to ASCII
    ascii_art = generator.convert_image(input_image)
    
    # Print result
    print(ascii_art)
    
    # Save to file
    generator.save_to_file(ascii_art, "basic_output.txt")
    print("Saved to basic_output.txt")

def enhanced_image_processing(input_image):
    """Using image processor for better results."""
    print("\n=== Enhanced Image Processing ===\n")
    
    # Create image processor
    processor = ImageProcessor()
    processor.load(input_image)
    
    # Apply enhancements
    processor.adjust_contrast(1.5)
    processor.adjust_brightness(1.2)
    processor.adjust_sharpness(1.3)
    processor.apply_unsharp_mask(radius=2, amount=1.5)
    
    # Get processed image
    processed_img = processor.get_processed_image()
    
    # Save processed image for inspection
    processor.save("enhanced_" + os.path.basename(input_image))
    print(f"Saved enhanced image to enhanced_{os.path.basename(input_image)}")
    
    # Create ASCII generator
    generator = ASCIIArtGenerator(width=80)
    
    # Convert processed image to ASCII
    ascii_image = generator._map_pixels_to_ascii(processed_img)
    ascii_art = '\n'.join([''.join(row) for row in ascii_image])
    
    # Print result
    print(ascii_art)
    
    # Save to file
    with open("enhanced_output.txt", 'w') as f:
        f.write(ascii_art)
    print("Saved to enhanced_output.txt")

def edge_detection_ascii(input_image):
    """Create ASCII art emphasizing edges."""
    print("\n=== Edge Detection ASCII ===\n")
    
    # Create image processor
    processor = ImageProcessor()
    processor.load(input_image)
    
    # Apply edge detection
    processor.detect_edges(mode="canny")
    
    # Get processed image
    processed_img = processor.get_processed_image()
    
    # Save processed image for inspection
    processor.save("edges_" + os.path.basename(input_image))
    print(f"Saved edge image to edges_{os.path.basename(input_image)}")
    
    # Create ASCII generator with inverted colors
    # (edges are white on black, for ASCII we want dark chars for edges)
    generator = ASCIIArtGenerator(width=80, invert=True)
    
    # Convert processed image to ASCII
    ascii_image = generator._map_pixels_to_ascii(processed_img)
    ascii_art = '\n'.join([''.join(row) for row in ascii_image])
    
    # Print result
    print(ascii_art)
    
    # Save to file
    with open("edges_output.txt", 'w') as f:
        f.write(ascii_art)
    print("Saved to edges_output.txt")

def custom_character_set(input_image):
    """Using a custom character set."""
    print("\n=== Custom Character Set ===\n")
    
    # Define a custom character set
    ASCIIArtGenerator.CHAR_SETS['custom'] = " .'`^\",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
    
    # Create generator with custom character set
    generator = ASCIIArtGenerator(width=80, char_set='custom')
    
    # Convert image to ASCII
    ascii_art = generator.convert_image(input_image)
    
    # Print result
    print(ascii_art)
    
    # Save to file
    generator.save_to_file(ascii_art, "custom_output.txt")
    print("Saved to custom_output.txt")

def high_detail_portrait(input_image):
    """Generate a high-detail ASCII portrait."""
    print("\n=== High Detail Portrait ===\n")
    
    # Create image processor
    processor = ImageProcessor()
    processor.load(input_image)
    
    # Apply portrait-optimized processing
    processor.resize(width=150)  # Wider for more detail
    processor.adjust_contrast(1.3)
    processor.adjust_brightness(1.1)
    processor.apply_unsharp_mask(radius=1.5, amount=1.8)
    
    # Get processed image
    processed_img = processor.get_processed_image()
    
    # Create generator with dense character set and dithering
    generator = ASCIIArtGenerator(
        width=150, 
        char_set='standard',
        dither=True
    )
    
    # Convert processed image to ASCII
    ascii_image = generator._map_pixels_to_ascii(processed_img)
    ascii_art = '\n'.join([''.join(row) for row in ascii_image])
    
    # Save to file (too large to print nicely)
    with open("portrait_output.txt", 'w') as f:
        f.write(ascii_art)
    print("Saved high-detail portrait to portrait_output.txt")
    
    # Create HTML version with small font
    html_content = f"""<!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>ASCII Art Portrait</title>
        <style>
            pre {{
                font-family: monospace;
                font-size: 8px;
                line-height: 0.9;
                white-space: pre;
                letter-spacing: 0.1em;
            }}
        </style>
    </head>
    <body>
        <pre>{ascii_art}</pre>
    </body>
    </html>"""
    
    with open("portrait_output.html", 'w') as f:
        f.write(html_content)
    print("Saved high-detail portrait to portrait_output.html")

def batch_processing(image_folder, output_folder):
    """Process multiple images in batch."""
    print(f"\n=== Batch Processing: {image_folder} -> {output_folder} ===\n")
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Create generator
    generator = ASCIIArtGenerator(width=100)
    
    # Process all images in folder
    for filename in os.listdir(image_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            input_path = os.path.join(image_folder, filename)
            output_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.txt")
            
            try:
                print(f"Processing {filename}...")
                ascii_art = generator.convert_image(input_path)
                generator.save_to_file(ascii_art, output_path)
                print(f"  Saved to {output_path}")
            except Exception as e:
                print(f"  Error processing {filename}: {e}")

def example_usage():
    """Demonstrate different usage examples."""
    if len(sys.argv) < 2:
        print("Usage: python usage_examples.py <image_path> [<image_folder> <output_folder>]")
        return
    
    input_image = sys.argv[1]
    
    if not os.path.exists(input_image):
        print(f"Error: Image not found: {input_image}")
        return
    
    # Basic usage
    basic_usage(input_image)
    
    # Enhanced image processing
    enhanced_image_processing(input_image)
    
    # Edge detection ASCII
    edge_detection_ascii(input_image)
    
    # Custom character set
    custom_character_set(input_image)
    
    # High detail portrait
    high_detail_portrait(input_image)
    
    # Batch processing (if folder paths provided)
    if len(sys.argv) >= 4:
        image_folder = sys.argv[2]
        output_folder = sys.argv[3]
        batch_processing(image_folder, output_folder)

if __name__ == "__main__":
    example_usage()
