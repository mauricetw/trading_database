# --- FILE: routers/seller.py ---
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload, contains_eager
from typing import List, Optional, Dict, Any
from datetime import datetime

# 1. 從 SQLAlchemy 引入 flag_modified
from sqlalchemy.orm.attributes import flag_modified

from database.db import get_db
from models.user import User
from models.product import Product, Category, ProductImage
from models.order import Order, OrderItem
from schemas.order_schema import OrderResponse, SellerOrderStatusUpdate
from schemas.product_schema import ProductCreate, ProductUpdate, ProductStatusUpdate, ProductResponse
from utils.token import get_current_user

router_seller = APIRouter(
    prefix="/seller", # 確保 main.py 中 app.include_router 是使用 /seller
    tags=["賣家中心 (Seller)"]
)

# ... (create_product 保持不變) ...
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
    category = db.query(Category).filter(Category.id == product_data.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="指定的分類不存在")

    # 使用 Pydantic V2 的 .model_dump()
    product_dict = product_data.model_dump(exclude={"image_urls"})
    
    new_product = Product(
        **product_dict,
        seller_id=current_user.id # 確保 seller_id 被設置
    )
    
    if product_data.image_urls:
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

    # 使用 Pydantic V2 的 .model_dump()
    update_data = product_data.model_dump(exclude_unset=True)
    
    if "image_urls" in update_data:
        # 處理圖片更新
        product.images.clear()
        db.flush() 
        if update_data["image_urls"]:
            for i, url in enumerate(update_data["image_urls"]):
                product.images.append(ProductImage(image_url=url, display_order=i))
        del update_data["image_urls"] # 從 update_data 中移除，避免 setattr 報錯

    # 更新其他欄位
    for key, value in update_data.items():
        setattr(product, key, value)
        
    # --- [BUG 修正] ---
    # 檢查是否需要自動更新狀態
    # 1. 如果賣家手動將庫存改為 0 或更少
    if "stock_quantity" in update_data and product.stock_quantity <= 0:
        product.status = "sold"
    # 2. 如果賣家手動補充庫存，且商品狀態是 'sold'
    elif "stock_quantity" in update_data and product.stock_quantity > 0 and product.status == "sold":
        product.status = "available" # 自動重新上架
        
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
    
    if not product:
        # 即使找不到，也回傳 204，不暴露資訊
        return None
        
    product.status = "archived"
    db.commit()
    
    return None

# --- 獲取賣家收到的所有訂單，並支援狀態篩選 ---
@router_seller.get("/orders", response_model=List[OrderResponse])
def get_my_orders_as_seller(
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

# --- 賣家獲取單一訂單詳情 ---
@router_seller.get("/orders/{order_id}", response_model=OrderResponse)
def get_seller_order_details(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """獲取單一訂單的詳細資訊，並驗證賣家是否有權限查看。"""
    order = db.query(Order).filter(Order.id == order_id).options(
        joinedload(Order.items).joinedload(OrderItem.product)
    ).first()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到訂單")

    is_seller_of_this_order = False
    for item in order.items:
        if item.product and item.product.seller_id == current_user.id:
            is_seller_of_this_order = True
            break

    if not is_seller_of_this_order:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="您沒有權限查看此訂單")

    return order


# --- 賣家更新訂單狀態 (一般) ---
@router_seller.patch("/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status_by_seller(
    order_id: int,
    status_update: SellerOrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """賣家更新指定訂單的狀態。"""
    # 2. [優化] 預先載入 (join) items 和 product
    order = db.query(Order).filter(Order.id == order_id).options(
        joinedload(Order.items).joinedload(OrderItem.product)
    ).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到訂單")
    
    # 3. 驗證權限 (現在更有效率)
    is_seller_of_this_order = False
    for item in order.items:
        if item.product and item.product.seller_id == current_user.id:
            is_seller_of_this_order = True
            break
            
    if not is_seller_of_this_order:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="您沒有權限修改此訂單")

    # 4. 更新狀態並新增歷史紀錄
    order.status = status_update.status
    
    new_history_entry = {
        "status": status_update.status,
        "timestamp": datetime.utcnow().isoformat(),
        "description": status_update.description or f"訂單狀態已由賣家更新為：{status_update.status}"
    }
    
    # 5. [修正] 處理 JSON 欄位更新 (假設 status_history 是 JSON 類型)
    if isinstance(order.status_history, list):
        order.status_history.append(new_history_entry)
    else:
        order.status_history = [new_history_entry]
    
    flag_modified(order, "status_history") # 告訴 SQLAlchemy 該 JSON 欄位已被修改

    db.commit()
    db.refresh(order)
    return order


# --- [新功能] 賣家標記訂單為「未取貨退回」並回補庫存 ---
@router_seller.patch("/orders/{order_id}/return", response_model=OrderResponse)
def mark_order_as_returned(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    賣家將「運送中」的訂單標記為「未取貨退回」。
    這會將訂單狀態設為 'failed'，並自動回補商品庫存。
    """
    
    try:
        # 1. 查找訂單 (不鎖定)
        order = db.query(Order).filter(Order.id == order_id).options(
            joinedload(Order.items).joinedload(OrderItem.product)
        ).first()

        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到訂單")

        # 2. 驗證權限 (不鎖定)
        is_seller_of_this_order = False
        product_ids_to_restock = []
        for item in order.items:
            if item.product and item.product.seller_id == current_user.id:
                is_seller_of_this_order = True
                product_ids_to_restock.append(item.product.id) # 收集需要回補的商品ID
                
        if not is_seller_of_this_order:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="您沒有權限修改此訂單")

        # 3. 驗證狀態 (不鎖定)
        if order.status != "delivering":
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"此訂單狀態為 '{order.status}'，無法標記為未取貨")

        # 4. [關鍵] 鎖定相關商品
        if product_ids_to_restock:
            # [BUG 修正] .with_for_update() 應在 .filter() 之後, .all() 之前
            locked_products = db.query(Product).filter(
                Product.id.in_(product_ids_to_restock)
            ).with_for_update().all()
            
            locked_product_map = {p.id: p for p in locked_products}

            # 5. [關鍵] 回補庫存
            print(f"訂單 {order.id} 退回，開始回補庫存...")
            for item in order.items:
                if item.product_id in locked_product_map:
                    locked_product = locked_product_map[item.product_id]
                    print(f"回補商品 {locked_product.id} 庫存 +{item.quantity}")
                    locked_product.stock_quantity += item.quantity
                    # 如果商品狀態是 'sold'，將其改回 'available'
                    if locked_product.status == "sold":
                        locked_product.status = "available"

        # 6. 更新訂單狀態
        order.status = "failed" # 未取貨 = 交易不成立
        
        new_history_entry = {
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat(),
            "description": "賣家標記：買家未取貨，訂單退回。"
        }
        if isinstance(order.status_history, list):
            order.status_history.append(new_history_entry)
        else:
            order.status_history = [new_history_entry]
        flag_modified(order, "status_history")

        # 7. 提交事務 (Transaction)
        db.commit()
        db.refresh(order)
        return order

    except Exception as e:
        db.rollback()
        print(f"處理訂單退回時發生錯誤: {e}")
        # 顯示更詳細的錯誤給前端 (可選)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"伺服器錯誤: {str(e)}")
