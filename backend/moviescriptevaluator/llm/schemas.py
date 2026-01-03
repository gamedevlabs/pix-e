from pydantic import BaseModel


class SimplifiedAssetMetaData(BaseModel):
    name: str
    class_name: str
    path: str
    usage_reason: str


class SceneBasedAnalysis(BaseModel):
    scene_id: str
    can_use_assets: bool
    assets_used: list[str]


class AssetListAnalysis(BaseModel):
    scenes: list[SceneBasedAnalysis]
