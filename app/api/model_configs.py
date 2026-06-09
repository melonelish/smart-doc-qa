from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet
import httpx

from app.core.config import get_settings
from app.db.database import get_db
from app.models.user import User
from app.models.model_config import ModelConfig
from app.api.deps import get_current_user
from app.services.qa_service import set_active_model_config

settings = get_settings()
router = APIRouter(prefix="/api/v1/model-configs", tags=["model-configs"])

# ── Preset providers (auto-fill base_url + model_name) ──
PRESET_PROVIDERS = {
    "deepseek": {
        "label": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "model_name": "deepseek-chat",
    },
    "openai": {
        "label": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "model_name": "gpt-4o-mini",
    },
    "qwen": {
        "label": "通义千问",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model_name": "qwen-turbo",
    },
    "doubao": {
        "label": "豆包",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model_name": "doubao-pro-32k",
    },
    "mimo": {
        "label": "小米 MiMo",
        "base_url": "https://api.mimo.xiaomi.com/v1",
        "model_name": "mimo-chat",
    },
    "custom": {
        "label": "自定义",
        "base_url": "",
        "model_name": "",
    },
}


def _get_fernet() -> Fernet:
    key = settings.encryption_key
    if len(key) < 32:
        key = key.ljust(32, "0")
    import base64
    import hashlib
    hash_key = base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest())
    return Fernet(hash_key)


def _encrypt(text: str) -> str:
    return _get_fernet().encrypt(text.encode()).decode()


def _decrypt(encrypted: str) -> str:
    return _get_fernet().decrypt(encrypted.encode()).decode()


# ── Request / response models ──

class ModelConfigCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    provider: str = Field(..., description="deepseek/openai/qwen/doubao/mimo/custom")
    base_url: str = Field(..., min_length=1, max_length=500)
    api_key: str = Field(..., min_length=1, max_length=500)
    model_name: str = Field(..., min_length=1, max_length=100)


class ModelConfigUpdate(BaseModel):
    name: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    model_name: str | None = None


class ModelConfigOut(BaseModel):
    id: str
    name: str
    provider: str
    base_url: str
    api_key_masked: str = ""
    model_name: str
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


def _to_out(mc: ModelConfig) -> ModelConfigOut:
    key = _decrypt(mc.api_key_encrypted)
    masked = key[:4] + "*" * max(0, len(key) - 8) + key[-4:] if len(key) > 8 else "****"
    return ModelConfigOut(
        id=mc.id,
        name=mc.name,
        provider=mc.provider,
        base_url=mc.base_url,
        api_key_masked=masked,
        model_name=mc.model_name,
        is_active=mc.is_active,
        created_at=mc.created_at.isoformat() if mc.created_at else "",
    )


# ── Endpoints ──

@router.get("/presets")
async def list_presets():
    """Return preset provider definitions for the frontend auto-fill."""
    return [
        {"key": k, "label": v["label"], "base_url": v["base_url"], "model_name": v["model_name"]}
        for k, v in PRESET_PROVIDERS.items()
    ]


@router.get("/", response_model=list[ModelConfigOut])
async def list_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    configs = (
        db.query(ModelConfig)
        .filter(ModelConfig.user_id == current_user.id)
        .order_by(ModelConfig.is_active.desc(), ModelConfig.created_at.desc())
        .all()
    )
    return [_to_out(c) for c in configs]


@router.post("/", response_model=ModelConfigOut)
async def create_config(
    body: ModelConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    encrypted_key = _encrypt(body.api_key)

    config = ModelConfig(
        user_id=current_user.id,
        name=body.name,
        provider=body.provider,
        base_url=body.base_url.rstrip("/"),
        api_key_encrypted=encrypted_key,
        model_name=body.model_name,
        is_active=False,
    )
    db.add(config)
    db.commit()
    db.refresh(config)

    # If this is the first config, auto-activate
    count = db.query(ModelConfig).filter(ModelConfig.user_id == current_user.id).count()
    if count == 1:
        config.is_active = True
        db.commit()
        # Apply to global LLM client
        api_key = _decrypt(config.api_key_encrypted)
        set_active_model_config(config.base_url, api_key, config.model_name)

    return _to_out(config)


@router.put("/{config_id}", response_model=ModelConfigOut)
async def update_config(
    config_id: str,
    body: ModelConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    config = (
        db.query(ModelConfig)
        .filter(ModelConfig.id == config_id, ModelConfig.user_id == current_user.id)
        .first()
    )
    if not config:
        raise HTTPException(status_code=404, detail="Model config not found")

    if body.name is not None:
        config.name = body.name
    if body.base_url is not None:
        config.base_url = body.base_url.rstrip("/")
    if body.api_key is not None:
        config.api_key_encrypted = _encrypt(body.api_key)
    if body.model_name is not None:
        config.model_name = body.model_name

    db.commit()
    db.refresh(config)
    return _to_out(config)


@router.delete("/{config_id}")
async def delete_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    config = (
        db.query(ModelConfig)
        .filter(ModelConfig.id == config_id, ModelConfig.user_id == current_user.id)
        .first()
    )
    if not config:
        raise HTTPException(status_code=404, detail="Model config not found")

    was_active = config.is_active
    db.delete(config)
    db.commit()

    # If deleted the active config, activate another
    if was_active:
        remaining = (
            db.query(ModelConfig)
            .filter(ModelConfig.user_id == current_user.id)
            .first()
        )
        if remaining:
            remaining.is_active = True
            db.commit()

    return {"message": "Deleted"}


@router.post("/{config_id}/activate")
async def activate_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    config = (
        db.query(ModelConfig)
        .filter(ModelConfig.id == config_id, ModelConfig.user_id == current_user.id)
        .first()
    )
    if not config:
        raise HTTPException(status_code=404, detail="Model config not found")

    # Deactivate all others
    db.query(ModelConfig).filter(
        ModelConfig.user_id == current_user.id,
        ModelConfig.id != config_id,
    ).update({"is_active": False})

    config.is_active = True
    db.commit()

    # Apply this config to the global LLM client so qa_service uses it
    api_key = _decrypt(config.api_key_encrypted)
    set_active_model_config(config.base_url, api_key, config.model_name)

    return {"message": "Activated", "config": _to_out(config).model_dump()}


@router.post("/{config_id}/test")
async def test_connection(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    config = (
        db.query(ModelConfig)
        .filter(ModelConfig.id == config_id, ModelConfig.user_id == current_user.id)
        .first()
    )
    if not config:
        raise HTTPException(status_code=404, detail="Model config not found")

    api_key = _decrypt(config.api_key_encrypted)
    url = f"{config.base_url}/chat/completions"

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": config.model_name,
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 5,
                },
            )
        if resp.status_code == 200:
            return {"status": "ok", "detail": "Connection successful"}
        else:
            return {"status": "error", "detail": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except httpx.ConnectError:
        return {"status": "error", "detail": "Cannot connect to API server"}
    except httpx.TimeoutException:
        return {"status": "error", "detail": "Connection timed out"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
