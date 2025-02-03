import base64
import pathlib
import sys
import unittest

# 获取当前文件的绝对路径，并逐级向上直到找到项目的根目录
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from app.routers.image_recognition import call_openai_recognize_image

class TestImageRecognition(unittest.TestCase):
    def test_call_openai_recognize_image(self):
        # Test case 1: Valid input image path
        image_path = "/code/eatup-backend/static/iShot_2025-02-02_23.43.57.png"
        file_type = "image/png"
        base64_image = encode_image(image_path)
        expected_output = "This is a test image."
        actual_output = call_openai_recognize_image(base64_image, file_type)
        self.assertEqual(actual_output, expected_output)

#  base 64 编码格式
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


if __name__ == "__main__":
    unittest.main()