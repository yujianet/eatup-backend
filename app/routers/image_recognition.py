import base64
import logging
import json

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from openai import OpenAI
from pydantic import BaseModel, Field
from pydantic_core import ValidationError

from app.config import settings


router = APIRouter(prefix="/image-recognition", tags=["image-recognition"])
logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=settings.AI_IMAGE_API_KEY,
    base_url=settings.AI_IMAGE_API_URL,
)

class FoodRecognitionResult(BaseModel):
    confidence: float = Field(..., ge=0, le=1, description="食物名判断的可信程度，0~1 之间小数")
    expiry_days: int = Field(..., description="食物的有效期，单位：天")
    food_name: str = Field(..., min_length=2, max_length=5, description="2~5 个字左右的食物名")

    def __init__(self, json_str: str):
        try:
            super().__init__(**json.loads(json_str))
        except ValidationError as e:
            raise ValueError(f"JSON 验证失败: {str(e)}")

@router.post("/", response_model=FoodRecognitionResult)
async def recognize_image(
        file: UploadFile = File(...),
):

    if file.content_type not in ['image/jpeg', 'image/png']:
        raise HTTPException(400, '仅支持JPEG/PNG格式')

    # 读取文件内容
    image_content = await file.read()

    # 进行 base64 编码
    base64_image = base64.b64encode(image_content).decode("utf-8")
    food_recognition = call_openai_recognize_image(base64_image, file.content_type)

    return food_recognition



def call_openai_recognize_image(base64_image: str, image_type: str) -> FoodRecognitionResult:
    # 定义系统提示词
    prompt = '''
你是一个谨慎的食品识别助手，请识别图片的主体部分，并返回符合以下 json schema 的输出，请谨慎判断。
食物的名称可能是各种水果、蔬菜、零食的名字，都是常见的东西。
当不确定时，food_name填'不清楚'。
{"type":"object","properties":{"confidence":{"type":"number","title":"置信度","minimum":0,"maximum":1,"exclusiveMinimum":0,"exclusiveMaximum":1,"description":"食物名判断的可信程度，0~1 之间小数},"expiry_days":{"type":"integer","description":"食物的有效期，单位：天","title":"有效期"},"food_name":{"type":"string","title":"食物名","description":"2~5 个字左右的食物名"}},"required":["confidence","expiry_days","food_name"]}
'''

    # 调用在线AI服务进行识别
    try:
        completion = client.chat.completions.create(
            model=settings.AI_IMAGE_MODEL,
            response_format = {"type": "json_object"},
            messages=[
                {
                    'role': 'system',
                    'content': [{'type': 'text', 'text': prompt}],
                },
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'image_url',
                            "image_url": {"url": f"data:{image_type};base64,{base64_image}"},
                        }
                    ],
                },
            ],
        )
    except Exception as e:
        err = IOError(f'AI服务调用失败: {str(e)}')
        logger.error(err.strerror)
        raise HTTPException(500, err.strerror)

    try:
        result = completion.choices[0].message.content
    except Exception as e:
        err = IOError(f'OpenAI兼容接口返回结构错误: {str(e)}')
        logger.error(err.strerror)
        raise HTTPException(500, err.strerror)

    try:
        food_recognition_result = FoodRecognitionResult(result)
    except Exception as e:
        err = IOError(f'OpenAI兼容接口返回结构错误: {str(e)}')
        logger.error(err.strerror)
        raise HTTPException(500, err.strerror)

    if food_recognition_result.food_name == '不清楚':
        food_recognition_result.confidence = 0.1
        food_recognition_result.expiry_days = 1
    return food_recognition_result
