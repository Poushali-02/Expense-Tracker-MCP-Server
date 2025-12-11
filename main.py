import random
from fastmcp import FastMCP

import qrcode
from PIL import Image

# Create a server instance
mcp = FastMCP(name="Expense Tracker Server")

# tool 1
@mcp.tool
def roll_dice(n_dice: int) -> list[int]:
    """Roll a dice between numbers 1 to 6 for given number of times"""
    return [random.randint(1,6) for _ in range(n_dice)]

# tool2 
@mcp.tool
def generate_qr_code(link, filename="qr_code.png"):
    """
    Generate a QR code for the given link
    
    Args:
        link (str): The URL or text to encode in the QR code
        filename (str): The output filename (default: qr_code.png)
    """
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,  # Controls the size of the QR code
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    # Add data to the QR code
    qr.add_data(link)
    qr.make(fit=True)
    
    # Create an image from the QR code
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save the image
    img.save(filename)
    print(f"QR code generated successfully and saved as '{filename}'")

if __name__ == "main":
    mcp.run()