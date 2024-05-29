from onevizion import Trackor, IntegrationLog, LogLevel
from module_error import ModuleError
from PIL import ImageDraw, ImageFont
from typing import Any, Dict, List
from io import BytesIO
import qrcode
import base64
import re

class Generator:
    def __init__(self, fill_color, back_color):
        self.back_color = back_color
        self.fill_color = fill_color

    def generate_qrcode(self, value, title):
        qr = qrcode.QRCode(version=1, box_size=12, border=6)
        qr.add_data(value); qr.make(fit=True)
        img = qr.make_image(back_color=self.back_color, fill_color=self.fill_color)
        qr_width, qr_height = img.size
        space_height = qr_height/6
        font = ImageFont.truetype("arial.ttf", 16)
        draw = ImageDraw.Draw(img)
        # Asset Name
        _, _, txt_width, txt_height = draw.textbbox((0, 0), text=title, font=font)
        draw.text(((qr_width-txt_width)/2, (space_height-txt_height)/2), text=title, fill=(255, 0, 0), font=font)
        # Asset ID
        _, _, txt_width, txt_height = draw.textbbox((0, 0), text=value, font=font)
        draw.text(((qr_width-txt_width)/2, ((qr_height-space_height)+(txt_height/2))), text=value, fill=(0, 0, 0), font=font)
        # Company Name
        # _, _, txt_width, txt_height = draw.textbbox((0, 0), text=company_name, font=font)
        # draw.text(((qr_width-txt_width)/2, ((qr_height-space_height)+(txt_height*2))), text=company_name, fill=(255, 0, 0), font=font)
        qrcode_bytes = BytesIO()
        img.save(qrcode_bytes, format='PNG')
        qrcode_bytes = qrcode_bytes.getvalue()
        qrcode_base64 = base64.b64encode(qrcode_bytes).decode('utf-8')
        return qrcode_base64

class OVAccessParameters:
    REGEXP_PROTOCOLS = '^(https|http)://'

    def __init__(self, ov_url: str, ov_access_key: str, ov_secret_key: str) -> None:
        self.ov_url_without_protocol = re.sub(OVAccessParameters.REGEXP_PROTOCOLS, '', ov_url)
        self.ov_access_key = ov_access_key
        self.ov_secret_key = ov_secret_key

class OVTrackor:
    def __init__(self, ov_source_access_parameters: OVAccessParameters):
        self._ov_url_without_protocol = ov_source_access_parameters.ov_url_without_protocol
        self._ov_access_key = ov_source_access_parameters.ov_access_key
        self._ov_secret_key = ov_source_access_parameters.ov_secret_key
        self._trackor_type_wrapper = Trackor()

    @property
    def trackor_type_wrapper(self) -> Trackor:
        return self._trackor_type_wrapper

    @trackor_type_wrapper.setter
    def trackor_type_wrapper(self, trackor_type_name: str):
        self._trackor_type_wrapper = Trackor(
            trackorType=trackor_type_name, URL=self._ov_url_without_protocol,
            userName=self._ov_access_key, password=self._ov_secret_key,
            isTokenAuth=True
        )

    def get_trackors_by_fields_and_search_trigger(self, fields_list: List[str], search_trigger: str) -> List[Dict[str, Any]]:
        self.trackor_type_wrapper.read(fields=fields_list, search=search_trigger)
        if len(self.trackor_type_wrapper.errors) > 0:
            raise ModuleError('Failed to get_trackors_by_fields_and_search_trigger', self.trackor_type_wrapper.errors)
        return list(self.trackor_type_wrapper.jsonData)

    def update_fields_by_trackor_id(self, trackor_id: int, field_dict: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        self.trackor_type_wrapper.update(trackorId=trackor_id, fields=field_dict)
        if len(self.trackor_type_wrapper.errors) > 0:
            raise ModuleError(f'Failed to update_fields_by_trackor_id', self.trackor_type_wrapper.errors)
        return self.trackor_type_wrapper.jsonData

class Module:
    TRACKOR_ID = 'TRACKOR_ID'

    def __init__(self, ov_module_log: IntegrationLog, settings_data: dict):
        self._module_log = ov_module_log
        self._settings = settings_data
        self._ov_access_parameters = OVAccessParameters(settings_data['ovUrl'], settings_data['ovAccessKey'], settings_data['ovSecretKey'])
        self._ov_trackor = OVTrackor(self._ov_access_parameters)
        self._generator = Generator(fill_color=settings_data["qrcodeFillColor"], back_color=settings_data["qrcodeBackgroudColor"])
        # Qrcode settings
        self._trackor_type = settings_data["trackorType"]
        self._qrcode_generate_field = settings_data["qrcodeGenerateField"]
        self._qrcode_image_field = settings_data["qrcodeImageField"]
        self._qrcode_title_field = settings_data["qrcodeTitleField"]
        self._qrcode_value_field = settings_data["qrcodeValueField"]

    def start(self):
        # self._module_log.add(LogLevel.INFO, 'Module is started')
        self._ov_trackor.trackor_type_wrapper = self._trackor_type
        qrcode_fields_list = [self._qrcode_title_field, self._qrcode_value_field]
        qrcode_search_trigger = f"equal({self._qrcode_generate_field}, 1)"
        asset_items = self._ov_trackor.get_trackors_by_fields_and_search_trigger(fields_list=qrcode_fields_list, search_trigger=qrcode_search_trigger)
        for asset_item in asset_items:
            trackor_id = asset_item[self.TRACKOR_ID]
            qrcode_value = asset_item[self._qrcode_value_field]
            qrcode_title = asset_item[self._qrcode_title_field]
            qrcode_bytes = self._generator.generate_qrcode(value=qrcode_value, title=qrcode_title)
            asset_item_fields = {
                self._qrcode_generate_field: '0',
                self._qrcode_image_field: {
                    "file_name": f"{qrcode_value}.png",
                    "data": qrcode_bytes
                }
            }
            self._ov_trackor.update_fields_by_trackor_id(trackor_id=trackor_id, field_dict=asset_item_fields)
            # self._module_log.add(LogLevel.INFO, f'Qrcode generated: trackor_id={trackor_id}, trackor_key={trackor_key}')

if __name__ == "__main__":
    import json
    with open('settings.json', 'rb') as settings_file:
        settings_data = json.loads(settings_file.read().decode('utf-8'))
    module = Module(ov_module_log=IntegrationLog, settings_data=settings_data)
    module.start()