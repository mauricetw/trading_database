from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from database.db import get_db
from models.product import Product
from models.user import User # 引入 User 模型以使用 get_current_user
from schemas.product_schema import ProductCreate, ProductResponse
from typing import List, Optional

# --- 引入 get_current_user 依賴 ---
from utils.token import get_current_user

router = APIRouter()

# --- 重構後的「上架商品」API ---
@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate, 
    db: Session = Depends(get_db),
    # --- 安全性修正：注入當前登入的使用者 ---
    current_user: User = Depends(get_current_user)
):
    """
    上架一個新商品。賣家 ID 將自動從認證 token 中獲取。
    """
    try:
        # --- 使用 .dict() 簡化模型轉換，並安全地插入 seller_id ---
        db_product = Product(
            **product_data.dict(), 
            seller_id=current_user.id
        )
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"建立商品時發生錯誤: {str(e)}"
        )

# --- 重構後的「獲取商品列表」API ---
@router.get("", response_model=List[ProductResponse])
async def get_all_products(
    db: Session = Depends(get_db),
    # --- 性能優化：增加分頁參數 ---
    skip: int = 0,
    limit: int = 20, # 預設每頁 20 個
    # --- 功能擴充：增加篩選與搜尋參數 ---
    category_id: Optional[int] = None,
    search: Optional[str] = None
):
    """
    獲取商品列表，支援分頁、分類篩選和關鍵字搜尋。
    """
    query = db.query(Product)

    # --- 性能優化：使用 joinedload 預先載入賣家資訊，避免 N+1 問題 ---
    query = query.options(joinedload(Product.seller))

    # 應用篩選條件
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    
    # 應用搜尋條件 (簡易版：搜尋名稱和描述)
    if search:
        query = query.filter(
            (Product.name.contains(search)) | (Product.description.contains(search))
        )

    # 應用分頁並執行查詢
    products = query.order_by(Product.created_at.desc()).offset(skip).limit(limit).all()
    
    return products


# --- 重構後的「獲取單一商品」API ---
@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    根據 ID 獲取單一商品的詳細資訊。
    """
    # --- 性能優化：同樣使用 joinedload ---
    product = db.query(Product).options(joinedload(Product.seller)).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="找不到此商品"
        )
    return product
