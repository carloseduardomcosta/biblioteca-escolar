import barcode
from barcode.writer import ImageWriter
import os

def gerar_barcode(code: str, output_folder: str) -> str:
    """Gera Code128 e salva em PNG, retorna nome do arquivo."""
    CODE128 = barcode.get_barcode_class('code128')
    filename = f"{code}.png"
    path = os.path.join(output_folder, filename)
    CODE128(code, writer=ImageWriter()).write(path)
    return filename
