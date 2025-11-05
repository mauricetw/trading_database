# --- FILE: routers/seller.py ---
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload, contains_eager
from typing import List, Optional
from datetime import datetime

from database.db import get_db
from models.user import User
from models.product import Product, Category, ProductImage
from models.order import Order, OrderItem
from schemas.order_schema import OrderResponse, SellerOrderStatusUpdate
from schemas.product_schema import ProductCreate, ProductUpdate, ProductStatusUpdate, ProductResponse
from utils.token import get_current_user

# --- 關鍵修正：將變數名稱從 router 改為 router_seller ---
# 這樣才能與 main.py 中的 app.include_router(seller.router_seller, ...) 匹配
router_seller = APIRouter(
    
    tags=["賣家中心 (Seller)"]
)

@router_seller.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_data: ProductCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    上架一個新商品。
    - **需要提供認證 Token**
    """
    # 檢查分類是否存在
    category = db.query(Category).filter(Category.id == product_data.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="指定的分類不存在")

    new_product = Product(
        **product_data.dict(exclude={"image_urls"}),
        seller_id=current_user.id
    )
    
    # 根據 image_urls 列表建立 ProductImage 紀錄
    for i, url in enumerate(product_data.image_urls):
        new_product.images.append(ProductImage(image_url=url, display_order=i))
        
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@router_seller.get("/products", response_model=List[ProductResponse])
def get_my_products(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    獲取當前登入賣家自己上架的所有商品。
    - **需要提供認證 Token**
    """
    return db.query(Product).filter(Product.seller_id == current_user.id).options(
        joinedload(Product.seller),
        joinedload(Product.category), 
        joinedload(Product.images)
    ).order_by(Product.created_at.desc()).all()

@router_seller.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int, 
    product_data: ProductUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    更新一件商品的資訊。
    - **需要提供認證 Token**
    - 只有商品擁有者才能更新。
    """
    product = db.query(Product).filter(
        Product.id == product_id, 
        Product.seller_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="找不到商品或您沒有權限")

    update_data = product_data.dict(exclude_unset=True)
    
    # 如果請求中包含 image_urls，則執行替換操作
    if "image_urls" in update_data:
        # 先刪除所有舊圖片
        product.images.clear()
        db.flush() # 立即將刪除操作同步到資料庫會話
        # 再新增所有新圖片
        for i, url in enumerate(update_data["image_urls"]):
            product.images.append(ProductImage(image_url=url, display_order=i))
        del update_data["image_urls"]

    # 更新其他欄位
    for key, value in update_data.items():
        setattr(product, key, value)
        
    db.commit()
    db.refresh(product)
    return product

@router_seller.patch("/products/{product_id}/status", response_model=ProductResponse)
def update_product_status(
    product_id: int, 
    status_data: ProductStatusUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    更新商品的狀態 (例如：上架/下架)。
    - **需要提供認證 Token**
    """
    product = db.query(Product).filter(Product.id == product_id, Product.seller_id == current_user.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="找不到商品或您沒有權限")
        
    product.status = status_data.status
    db.commit()
    db.refresh(product)
    return product

@router_seller.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    對一件商品進行「軟刪除」(Soft Delete)。
    - 將商品的狀態標記為 'archived' (已封存)。
    - 只有商品擁有者才能操作。
    """
    product = db.query(Product).filter(
        Product.id == product_id, 
        Product.seller_id == current_user.id
    ).first()
    
    # 即使找不到商品，也回傳成功，避免讓攻擊者知道商品是否存在
    if not product:
        return None
        
    # 將狀態更新為 'archived'，而不是從資料庫中刪除
    product.status = "archived"
    db.commit()
    
    return None

# --- 獲取賣家收到的所有訂單，並支援狀態篩選 ---
@router_seller.get("/orders", response_model=List[OrderResponse])
def get_my_orders_as_seller(
    # --- 關鍵修正：在 description 中清楚說明可用的篩選選項 ---
    status: Optional[str] = Query(None, description="根據訂單狀態篩選 (pending, failed, completed, rejected)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """獲取當前登入賣家收到的所有訂單。"""
    query = (
        db.query(Order)
        .join(Order.items)
        .join(OrderItem.product)
        .filter(Product.seller_id == current_user.id)
        .options(
            contains_eager(Order.items).joinedload(OrderItem.product)
        )
        .distinct()
    )

    if status:
        query = query.filter(Order.status == status)

    orders = query.order_by(Order.created_at.desc()).all()
    return orders

# --- 賣家更新訂單狀態 ---
@router_seller.patch("/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status_by_seller(
    order_id: int,
    status_update: SellerOrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """賣家更新指定訂單的狀態。"""
    # 1. 查找訂單
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到訂單")
    
    # 2. 驗證權限
    is_seller_of_this_order = (
        db.query(OrderItem)
        .join(Product)
        .filter(
            OrderItem.order_id == order_id,
            Product.seller_id == current_user.id
        )
        .first() is not None
    )
    if not is_seller_of_this_order:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="您沒有權限修改此訂單")

    # 3. 更新狀態並新增歷史紀錄
    order.status = status_update.status
    
    new_history_entry = {
        "status": status_update.status,
        "timestamp": datetime.utcnow().isoformat(),
        "description": status_update.description or f"訂單狀態已由賣家更新為：{status_update.status}"
    }
    
    if order.status_history:
        order.status_history.append(new_history_entry)
    else:
        order.status_history = [new_history_entry]
    
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(order, "status_history")

    db.commit()
    db.refresh(order)
    return order
