import traceback
import logging

from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel


logging.getLogger("transformers").setLevel(logging.ERROR)


def trocr(image_path):
    try:
        image = Image.open(image_path).convert("RGB")

        processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-printed')
        model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-printed')
        pixel_values = processor(images=image, return_tensors="pt").pixel_values

        generated_ids = model.generate(pixel_values, max_length=6)
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return generated_text
    except Exception as e:
        print(traceback.format_exc())
        print(e)
        return None
