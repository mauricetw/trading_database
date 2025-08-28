from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

from database.db import get_db
from models.user import User
from models.product import Product, Category, ProductImage
from schemas.product_schema import ProductCreate, ProductUpdate, ProductStatusUpdate, ProductResponse
from utils.token import get_current_user

# 初始化 API Router
router = APIRouter(
    prefix="/seller",
    tags=["賣家中心 (Seller)"]
)

@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_data: ProductCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    上架一個新商品。
    - **需要提供認證 Token**
    """
    if not db.query(Category).filter(Category.id == product_data.category_id).first():
        raise HTTPException(status_code=404, detail="指定的分類不存在")

    new_product = Product(
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        original_price=product_data.original_price,
        stock_quantity=product_data.stock_quantity,
        tags=product_data.tags,
        seller_id=current_user.id,
        category_id=product_data.category_id
    )
    
    # 根據 image_urls 列表建立 ProductImage 紀錄
    for i, url in enumerate(product_data.image_urls):
        new_product.images.append(ProductImage(image_url=url, display_order=i))
        
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@router.get("/products", response_model=List[ProductResponse])
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

@router.put("/products/{product_id}", response_model=ProductResponse)
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
    product = db.query(Product).options(
        joinedload(Product.seller), 
        joinedload(Product.category), 
        joinedload(Product.images)
    ).filter(Product.id == product_id, Product.seller_id == current_user.id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="找不到商品或您沒有權限")

    update_data = product_data.dict(exclude_unset=True)
    
    # 如果請求中包含 image_urls，則執行替換操作
    if "image_urls" in update_data:
        # 先刪除所有舊圖片
        for image in product.images:
            db.delete(image)
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

@router.patch("/products/{product_id}/status", response_model=ProductResponse)
def update_product_status(
    product_id: int, 
    status_data: ProductStatusUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    更新商品的狀態 (例如：上架/下架)。
    - **需要提供認證 Token**
    - 只有商品擁有者才能更新。
    """
    product = db.query(Product).filter(Product.id == product_id, Product.seller_id == current_user.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="找不到商品或您沒有權限")
        
    product.status = status_data.status
    db.commit()
    db.refresh(product)
    return product

@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    刪除一件商品。
    - **需要提供認證 Token**
    - 只有商品擁有者才能刪除。
    """
    product = db.query(Product).filter(Product.id == product_id, Product.seller_id == current_user.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="找不到商品或您沒有權限")
        
    db.delete(product)
    db.commit()
    return None
