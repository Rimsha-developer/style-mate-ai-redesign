
import mediapipe as mp
import os

class FashionPosePipeline:

    def __init__(self, model_path):
        if not os.path.exists(model_path):
            raise FileNotFoundError(model_path)

        options = mp.tasks.vision.PoseLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(
                model_asset_path=model_path
            ),
            running_mode=mp.tasks.vision.RunningMode.IMAGE
        )

        self.landmarker = (
            mp.tasks.vision.PoseLandmarker.create_from_options(
                options
            )
        )

    def detect(self, image_rgb):
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=image_rgb
        )

        result = self.landmarker.detect(mp_image)

        if not result.pose_landmarks:
            return None

        return result.pose_landmarks[0]

    def close(self):
        self.landmarker.close()
