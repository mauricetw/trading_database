from pydantic import BaseModel, Field
from typing import Optional
from pydantic.alias_generators import to_camel

# --- 重大修正 ---
# 這裡修正了幾個問題：
# 1. 欄位名稱從駝峰式 (avatarUrl) 改為與資料庫模型一致的蛇形 (avatar_url)。
# 2. `id` 的類型從 `str` 修正為 `int`。
# 3. 使用 Pydantic 的 AliasGenerator，讓 Python 內部使用蛇形命名，
#    但在序列化成 JSON 給前端時，自動轉換為駝峰式命名。這是處理命名風格差異的最佳實踐。

class UserPublicProfile(BaseModel):
    # 在 Python 程式碼中使用 snake_case
    id: int
    username: str
    avatar_url: Optional[str] = None
    school_name: Optional[str] = None
    buyer_rating: Optional[float] = None
    seller_rating: Optional[float] = None

    class Config:
        orm_mode = True
        # 設定別名生成器，輸出 JSON 時會自動轉成駝峰式
        alias_generator = to_camel
        # 允許 Pydantic 使用別名來填充模型
        populate_by_name = True


# 保持與你原本設計一致的巢狀結構
class UserProfileResponse(BaseModel):
    user: UserPublicProfile

    class Config:
        alias_generator = to_camel
        populate_by_name = True
