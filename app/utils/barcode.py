import barcode
from barcode.writer import ImageWriter
import os

def gerar_barcode(code: str, output_folder: str) -> str:
    """Gera Code128 (apenas barras, sem número embutido) e salva em PNG.

    O número legível é desenhado em vetor pelo PDF da etiqueta — assim não
    fica distorcido quando a imagem é esticada para caber na etiqueta.
    """
    CODE128 = barcode.get_barcode_class('code128')
    filename = f"{code}.png"
    path = os.path.join(output_folder, filename)
    CODE128(code, writer=ImageWriter()).write(
        path,
        options={'write_text': False, 'module_height': 12.0, 'quiet_zone': 2.0},
    )
    return filename
