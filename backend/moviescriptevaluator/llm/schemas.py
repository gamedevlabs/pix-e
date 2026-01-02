from pydantic import BaseModel

class SceneBasedAnalysis(BaseModel):
    scene_id: str
    can_use_assets: bool
    assets_used: list[str]

class AssetListAnalysis(BaseModel):
    scenes: list[SceneBasedAnalysis]

