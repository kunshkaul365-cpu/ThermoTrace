
import os
from typing import Literal, Tuple

VALID_MODES: Tuple[str, ...] = ("DEMO", "LIVE")
Mode = Literal["DEMO", "LIVE"]


class Settings:
    def __init__(self) -> None:
        raw_mode = os.environ.get("MODE", "DEMO").strip().upper()
        if raw_mode not in VALID_MODES:
            raise ValueError(
                f"Invalid MODE={raw_mode!r}. MODE must be one of {VALID_MODES}."
            )
        self.mode: Mode = raw_mode  
        self.aoi_bbox: Tuple[float, float, float, float] = (68.0, 6.0, 97.5, 37.5)
        self.sample_data_path: str = os.environ.get(
            "SAMPLE_DATA_PATH", "sample/assessments.json"
        )


settings = Settings()
