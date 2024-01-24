import traceback
import logging

from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel


logging.getLogger("transformers").setLevel(logging.ERROR)


class TROCR:
    def __init__(self):
        self.processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-printed')
        self.model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-printed')

    def trocr(self, image_path):
        try:
            image = Image.open(image_path).convert("RGB")
            pixel_values = self.processor(images=image, return_tensors="pt").pixel_values

            generated_ids = self.model.generate(pixel_values, max_length=6)
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            return generated_text
        except Exception as e:
            print(traceback.format_exc())
            print(e)
            return None
