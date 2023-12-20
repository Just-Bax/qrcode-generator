from io import BytesIO
import qrcode
import base64

class Generator:

    def __init__(self, fill_color, back_color):
        self.back_color = back_color
        self.fill_color = fill_color

    def generate_qrcode(self, value):
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(value); qr.make(fit=True)
        img = qr.make_image(fill_color=self.fill_color, back_color=self.back_color)
        qrcode_bytes = BytesIO()
        img.save(qrcode_bytes, format='PNG')
        qrcode_bytes = qrcode_bytes.getvalue()
        qrcode_base64 = base64.b64encode(qrcode_bytes).decode('utf-8')
        return qrcode_base64