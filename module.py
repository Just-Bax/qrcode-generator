from onevizion import Trackor, IntegrationLog
from module_error import ModuleError
from typing import Any, Dict, List
from generator import Generator
import re

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

    def get_trackor_by_filters(self, trackor_key: str, filter_dict: Dict[str, str]) -> List[Dict[str, Any]]:
        self.trackor_type_wrapper.read(filters=filter_dict)

        if len(self.trackor_type_wrapper.errors):
            raise ModuleError(
                f'Failed to get_trackor_by_filters for {trackor_key}',
                self.trackor_type_wrapper.errors
            )

        return list(self.trackor_type_wrapper.jsonData)

    def get_trackors_by_fields_and_search_trigger(self, fields_list: List[str], search_trigger: str) -> List[Dict[str, Any]]:
        self.trackor_type_wrapper.read(
            fields=fields_list, search=search_trigger
        )

        if len(self.trackor_type_wrapper.errors) > 0:
            raise ModuleError('Failed to get_trackors_by_fields_and_search_trigger', self.trackor_type_wrapper.errors)

        return list(self.trackor_type_wrapper.jsonData)

    def update_fields_by_trackor_id(self, trackor_key: str, trackor_id: int, field_dict: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        self.trackor_type_wrapper.update(
            trackorId=trackor_id, fields=field_dict
        )

        if len(self.trackor_type_wrapper.errors) > 0:
            raise ModuleError(
                f'Failed to update_fields_by_trackor_id for {trackor_key}',
                self.trackor_type_wrapper.errors
            )

        return self.trackor_type_wrapper.jsonData

    def clean_trackor_trigger_by_filters(self, trackor_key: str, filter_dict: Dict[str, Any], field_dict: Dict[str, Any]):
        self.trackor_type_wrapper.update(
            filters=filter_dict, fields=field_dict
        )

        if len(self.trackor_type_wrapper.errors) > 0:
            raise ModuleError(
                f'Failed to clean_trackor_trigger_by_filters for {trackor_key}',
                self.trackor_type_wrapper.errors
            )

class Module:
    ASSET_ITEM_TRACKOR_TYPE = 'VHMECT_ASSET_ITEM'
    GENERATE_QRCODE_FIELDNAME = 'VHMECT_ECAI_GENERATE_QR_CODE'
    QRCODE_FIELDNAME = 'VHMECT_ECAI_ASSET_QR_CODE'
    LOG_TRACKOR_KEY = 'Asset Item Trackor Key'
    
    def __init__(self, ov_module_log: IntegrationLog, settings_data: dict):
        self._module_log = ov_module_log
        self._settings = settings_data
        self._ov_source_access_parameters = OVAccessParameters(settings_data['ovUrl'], settings_data['ovAccessKey'], settings_data['ovSecretKey'])
        self._ov_source_trackor = OVTrackor(self._ov_source_access_parameters)
        self.generator = Generator(fill_color="#152B42", back_color="transparent")

    def start(self):
        # self._module_log.add(LogLevel.INFO, 'Module is started')

        self._ov_source_trackor.trackor_type_wrapper = self.ASSET_ITEM_TRACKOR_TYPE
        asset_item_filter = {
            self.GENERATE_QRCODE_FIELDNAME: '1'
        }
        asset_item_trackors = self._ov_source_trackor.get_trackor_by_filters(trackor_key=self.LOG_TRACKOR_KEY, filter_dict=asset_item_filter)
        for asset_item_trackor in asset_item_trackors:
            trackor_id = asset_item_trackor['TRACKOR_ID']
            trackor_key = asset_item_trackor['TRACKOR_KEY']
            qrcode_bytes = self.generator.generate_qrcode(value=trackor_key)
            asset_item_fields = {
                self.GENERATE_QRCODE_FIELDNAME: '0',
                self.QRCODE_FIELDNAME: {"file_name": "qrcode.png", "data": qrcode_bytes}
            }
            update_result = self._ov_source_trackor.update_fields_by_trackor_id(trackor_key=self.LOG_TRACKOR_KEY, trackor_id=trackor_id, field_dict=asset_item_fields)
            print(update_result)

if __name__ == "__main__":
    settings = {
        "ovUrl": "https://cloud-erp.onevizion.com", 
        "ovAccessKey": "22smb8jNovkaKnRUKawH", 
        "ovSecretKey": "jPWKtZ9tG7qFv6ZMuhtQCTvJ1RR3tS4NvErieer3VnrwcdZtYa48brZWBahO51wDegoK4n"
    }
    module = Module(ov_module_log=IntegrationLog, settings_data=settings)
    module.start()