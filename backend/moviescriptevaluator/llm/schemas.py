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


class ScriptSceneAnalysis(BaseModel):
    scene: str
    asset_name: str
    asset_type: str
    fab_search_keyword: str
    notes: str


class MovieScriptAnalysis(BaseModel):
    result: list[ScriptSceneAnalysis]


class RecommendationResultItem(BaseModel):
    scene: str
    asset_id: str
    asset_name: str
    asset_class_name: str
    purpose: str
    description: str


class RecommendationResult(BaseModel):
    result: list[RecommendationResultItem]
