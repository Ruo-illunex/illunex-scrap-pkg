import traceback

from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

from app.common.log.log_config import setup_logger
from app.common.core.utils import make_dir, get_current_datetime
from app.config.settings import FILE_PATHS, TROCR_MODEL_PATH


class TROCR:
    def __init__(self):
        self._processor = TrOCRProcessor.from_pretrained(TROCR_MODEL_PATH)
        self._model = VisionEncoderDecoderModel.from_pretrained(TROCR_MODEL_PATH)
        self._log_path = FILE_PATHS['log'] + 'trocr'
        make_dir(self._log_path)
        self._log_file = self._log_path + f'/{get_current_datetime()}.log'
        self._logger = setup_logger(
            'trocr',
            self._log_file
        )

    async def trocr(self, image: Image) -> str:
        """TROCR을 이용해 이미지에서 텍스트를 추출하는 함수
        args:
            image: PIL.Image로 변환된 객체 (Image.open(image_path).convert("RGB"))
        returns:
            generated_text: 추출된 텍스트
        """
        try:
            pixel_values = self._processor(
                images=image, return_tensors="pt").pixel_values

            generated_ids = self._model.generate(pixel_values, max_length=6)
            generated_text = self._processor.batch_decode(
                generated_ids, skip_special_tokens=True)[0]
            return generated_text
        except Exception as e:
            err_msg = f'Error in trocr: {e}\n{traceback.format_exc()}'
            self._logger.error(err_msg)
            return None
