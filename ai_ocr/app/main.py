import traceback
import io

from fastapi import FastAPI, UploadFile
from PIL import Image

from app.common.core.trocr import TROCR
from app.config.settings import FILE_PATHS
from app.common.log.log_config import setup_logger
from app.common.core.utils import get_current_datetime, make_dir


# 로거 설정
current_time = get_current_datetime()
file_path = FILE_PATHS["log"] + 'main_logger'
make_dir(file_path)
file_path += f'/main_{current_time}.log'
logger = setup_logger(
    "main_logger",
    file_path,
)

app = FastAPI()
trocr_model = TROCR()


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/api/v1/trocr")
async def get_text_from_trocr(image: UploadFile) -> dict:
    """TROCR을 이용해 이미지에서 텍스트를 추출하는 함수
    args:
        image: PIL.Image로 변환된 객체 (Image.open(image_path).convert("RGB"))
    returns:
        dictionary: {status: 상태 메시지, text: 추출된 텍스트}
    """
    logger.info("--------------------------------------------------")
    logger.info("TROCR started...")
    try:
        image_bytes = await image.read()
        image_pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        text = await trocr_model.trocr(image=image_pil)
        return {"status": 200, "text": text}
    except Exception as e:
        err_msg = f"Error: {e}\n{traceback.format_exc()}"
        logger.error(err_msg)
        return {"status": 500, "text": None}
    finally:
        logger.info("TROCR completed...")
        logger.info("--------------------------------------------------")
