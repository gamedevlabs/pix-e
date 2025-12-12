from pydantic import BaseModel


class AssetListAnalysis(BaseModel):
    scene_description: str
    elements: list[str]
