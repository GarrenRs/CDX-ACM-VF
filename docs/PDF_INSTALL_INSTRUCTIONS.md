PDF Generation - Troubleshooting and Installation

If you see errors similar to:

"Error generating PDF: cannot load library 'libgobject-2.0-0'" or "ctypes.util.find_library() did not manage to locate a library called 'libgobject-2.0-0'",

this means WeasyPrint's native GTK/Cairo/Pango dependencies are not available on your system (common on Windows).

Options to resolve:

1) Install WeasyPrint dependencies (recommended if you want WeasyPrint):

- On Windows (MSYS2):
  - Install MSYS2 following https://www.msys2.org/
  - Open MSYS2 MinGW 64-bit shell and run:
    - pacman -Syu
    - pacman -S mingw-w64-x86_64-gtk3 mingw-w64-x86_64-python3-gobject mingw-w64-x86_64-cairo mingw-w64-x86_64-gdk-pixbuf
  - Add the `mingw64/bin` directory to your PATH so Python can load the libraries.
  - See WeasyPrint docs: https://weasyprint.readthedocs.io/en/latest/install.html#windows

2) Use wkhtmltopdf + pdfkit (fallback):

- Install wkhtmltopdf for Windows from https://wkhtmltopdf.org/downloads.html and place the binary on your PATH.
- Install the Python wrapper: pip install pdfkit
- The application will automatically use wkhtmltopdf/pdfkit if WeasyPrint is unavailable.

3) Container / Linux alternative (easier in many CI / server environments):

- Use the WeasyPrint packages available in Linux package managers (apt, yum) or use the official docs for Linux installation.
- Example (Ubuntu): sudo apt install libpango-1.0-0 libcairo2 libgdk-pixbuf2.0-0 libgobject-2.0-0

If you're unsure, use wkhtmltopdf as it's simple to install and works reliably on Windows.

If you want, I can add automated checks or a setup script to help install these dependencies on Windows.
