from sqlalchemy.orm import Session
from app.models.business import Customers, CollectionPoint, DailyPurchases, Partners, PartnerBusinesses, Investment, DailyPayment
from app.models.inventory import MaterialPurchase, Inventory, InventoryExport, ProductTransaction
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.schemas.daily_purchase import DailyPurchaseCreate, DailyPurchaseUpdate
from app.schemas.partner import PartnerCreate, PartnerUpdate
from app.schemas.partner_business import PartnerBusinessCreate, PartnerBusinessUpdate
from app.schemas.investment import InvestmentCreate, InvestmentUpdate
from app.schemas.daily_payment import DailyPaymentCreate
from app.schemas.inventory import InventoryUpdate
from typing import Optional, List
from datetime import date
from uuid import UUID
from bot.utils.logger import LogInfo

def get_customers_with_collection_name(
    db: Session,
    ingredient: Optional[str] = None,
    collection_point_id: Optional[str] = None,
    hoursehold_id: Optional[str] = None,
) -> List[dict]:
    """
    Get all customers with their associated collection point name.
    Optionally filter by ingredient, collection_point_id, or hoursehold_id.
    """
    query = db.query(Customers, CollectionPoint.collection_name).outerjoin(
        CollectionPoint, Customers.collection_point_id == CollectionPoint.id
    )
    
    if ingredient is not None:
        cleaned_ingredient = ingredient.strip().strip("'").strip('"').strip()
        if cleaned_ingredient.startswith("!="):
            val = cleaned_ingredient[2:].strip()
            query = query.filter(
                ~Customers.ingredient.ilike(val),
                # Customers.ingredient != "",
                # Customers.ingredient.is_not(None)
            )
        else:
            query = query.filter(Customers.ingredient.ilike(cleaned_ingredient))
        
    if collection_point_id is not None:
        query = query.filter(Customers.collection_point_id == collection_point_id)
        
    if hoursehold_id is not None:
        query = query.filter(Customers.hoursehold_id == hoursehold_id)
        
    results = query.all()
    
    data = []
    for customer, collection_name in results:
        customer_dict = {
            "id": customer.id,
            "fullname": customer.fullname,
            "hoursehold_id": customer.hoursehold_id,
            "collection_point_id": customer.collection_point_id,
            "number_phone": customer.number_phone,
            "address": customer.address,
            "ingredient": customer.ingredient,
            "amount_of_debt": customer.amount_of_debt,
            "cash_advance": customer.cash_advance,
            "total_debt": customer.total_debt,
            "status": customer.status,
            "username": customer.username,
            "telegram_group": customer.telegram_group,
            "number_bank": customer.number_bank,
            "bank_name": customer.bank_name,
            "is_subsidized": customer.is_subsidized,
            "collection_name": collection_name
        }
        data.append(customer_dict)
        
    return data

def get_collection_points_by_ingredient(db: Session, ingredient: Optional[str] = None) -> List[CollectionPoint]:
    """
    Get distinct collection points that have customers with the specified ingredient.
    If ingredient is None, return all collection points.
    """
    if not ingredient:
        return db.query(CollectionPoint).all()
        
    cleaned_ingredient = ingredient.strip().strip("'").strip('"').strip()
    query = db.query(CollectionPoint).join(
        Customers, Customers.collection_point_id == CollectionPoint.id
    )
    
    if cleaned_ingredient.startswith("!="):
        val = cleaned_ingredient[2:].strip()
        query = query.filter(
            ~Customers.ingredient.ilike(val),
            Customers.ingredient != "",
            Customers.ingredient.is_not(None)
        )
    else:
        query = query.filter(Customers.ingredient.ilike(cleaned_ingredient))
        
    return query.distinct().all()


def create_customer(db: Session, obj_in: CustomerCreate) -> Customers:
    """
    Create a new customer in the database.
    """
    db_obj = Customers(
        id=obj_in.id,
        fullname=obj_in.fullname,
        hoursehold_id=obj_in.hoursehold_id,
        collection_point_id=obj_in.collection_point_id,
        number_phone=obj_in.number_phone,
        address=obj_in.address,
        ingredient=obj_in.ingredient,
        amount_of_debt=obj_in.amount_of_debt,
        cash_advance=obj_in.cash_advance,
        total_debt=obj_in.total_debt,
        status=obj_in.status,
        username=obj_in.username,
        telegram_group=obj_in.telegram_group,
        number_bank=obj_in.number_bank,
        bank_name=obj_in.bank_name,
        is_subsidized=obj_in.is_subsidized,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_daily_purchases_detailed(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    hoursehold_id: Optional[str] = None,
    product_code: Optional[str] = None,
    collection_point_id: Optional[str] = None,
) -> List[dict]:
    """
    Get detailed daily purchases joined with Customers and CollectionPoints.
    Includes optional filters.
    """
    query = db.query(
        DailyPurchases,
        Customers.fullname,
        CollectionPoint.collection_name
    ).outerjoin(
        Customers, DailyPurchases.hoursehold_id == Customers.hoursehold_id
    ).outerjoin(
        CollectionPoint, DailyPurchases.collection_point_id == CollectionPoint.id
    )

    if start_date:
        query = query.filter(DailyPurchases.day >= start_date)
    if end_date:
        query = query.filter(DailyPurchases.day <= end_date)
    if hoursehold_id:
        query = query.filter(DailyPurchases.hoursehold_id == hoursehold_id)
    if product_code:
        query = query.filter(DailyPurchases.product_code.ilike(f"%{product_code.strip()}%"))
    if collection_point_id:
        query = query.filter(DailyPurchases.collection_point_id == collection_point_id)

    results = query.all()

    data = []
    for dp, fullname, collection_name in results:
        data.append({
            "id": dp.id,
            "hoursehold_id": dp.hoursehold_id,
            "fullname": fullname,
            "collection_name": collection_name,
            "day": dp.day,
            "is_subsidized": dp.is_subsidized,
            "weight": dp.weight,
            "tare_weight": dp.tare_weight,
            "actual_weight": dp.actual_weight,
            "degree": dp.degree,
            "dry_rubber": dp.dry_rubber,
            "unit_price": dp.unit_price,
            "subsidy_price": dp.subsidy_price,
            "total_amount": dp.total_amount,
            "paid_amount": dp.paid_amount,
            "saved_amount": dp.saved_amount,
            "product_code": dp.product_code,
        })
    return data


def create_daily_purchase(db: Session, obj_in: DailyPurchaseCreate) -> DailyPurchases:
    """
    Create a new daily purchase record in the database.
    """
    db_obj = DailyPurchases(
        hoursehold_id=obj_in.hoursehold_id,
        collection_point_id=obj_in.collection_point_id,
        product_code=obj_in.product_code,
        week=obj_in.week,
        day=obj_in.day,
        is_subsidized=obj_in.is_subsidized,
        weight=obj_in.weight,
        tare_weight=obj_in.tare_weight,
        actual_weight=obj_in.actual_weight,
        degree=obj_in.degree,
        dry_rubber=obj_in.dry_rubber,
        unit_price=obj_in.unit_price,
        subsidy_price=obj_in.subsidy_price,
        total_amount=obj_in.total_amount,
        paid_amount=obj_in.paid_amount,
        saved_amount=obj_in.saved_amount,
        advance_amount=0.0,
        is_checked=False
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_customer(db: Session, customer_id: str, obj_in: CustomerUpdate) -> Optional[Customers]:
    """
    Update an existing customer in the database.
    """
    db_obj = db.query(Customers).filter(Customers.id == customer_id).first()
    if not db_obj:
        return None
    
    update_data = obj_in.dict(exclude_unset=True)
    if "id" in update_data:
        del update_data["id"]
        
    for field, value in update_data.items():
        setattr(db_obj, field, value)
        
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_customer(db: Session, customer_id: str) -> Optional[Customers]:
    """
    Delete an existing customer from the database.
    """
    db_obj = db.query(Customers).filter(Customers.id == customer_id).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj


def update_daily_purchase(db: Session, purchase_id: UUID, obj_in: DailyPurchaseUpdate) -> Optional[DailyPurchases]:
    """
    Update an existing daily purchase in the database.
    """
    db_obj = db.query(DailyPurchases).filter(DailyPurchases.id == purchase_id).first()
    if not db_obj:
        return None
    
    update_data = obj_in.dict(exclude_unset=True)
    if "id" in update_data:
        del update_data["id"]
        
    for field, value in update_data.items():
        setattr(db_obj, field, value)
        
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_daily_purchase(db: Session, purchase_id: UUID) -> Optional[DailyPurchases]:
    """
    Delete a daily purchase from the database.
    """
    db_obj = db.query(DailyPurchases).filter(DailyPurchases.id == purchase_id).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj


def get_material_purchases_detailed(
    db: Session,
    material_type: Optional[str] = None,
    storage_name: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[dict]:
    """
    Get all material purchases joined with Customers to get the customer's fullname.
    Optionally filter by material_type or storage_name, and date range.
    """
    query = db.query(
        MaterialPurchase,
        Customers.fullname
    ).outerjoin(
        Customers, MaterialPurchase.customer_id == Customers.hoursehold_id
    )
    
    if material_type is not None:
        cleaned_material_type = material_type.strip().strip("'").strip('"').strip()
        query = query.filter(MaterialPurchase.material_type.ilike(cleaned_material_type))
        
    if storage_name is not None:
        cleaned_storage_name = storage_name.strip().strip("'").strip('"').strip()
        query = query.filter(MaterialPurchase.storage_name.ilike(cleaned_storage_name))

    if start_date is not None:
        query = query.filter(MaterialPurchase.transaction_date >= start_date)

    if end_date is not None:
        query = query.filter(MaterialPurchase.transaction_date <= end_date)

    results = query.all()
    
    data = []
    for mp, fullname in results:
        data.append({
            "id": mp.id,
            "transaction_date": mp.transaction_date,
            "customer_id": mp.customer_id,
            "fullname": fullname,
            "material_type": mp.material_type,
            "storage_name": mp.storage_name,
            "trip_count": mp.trip_count,
            "weight": mp.weight,
            "unit_price": mp.unit_price,
            "total_amount": mp.total_amount,
            "advance_payment": mp.advance_payment,
            "debt": mp.debt,
            "notes": mp.notes
        })
    return data


def create_material_purchase(db: Session, obj_in) -> MaterialPurchase:
    """
    Create a new material purchase record in the database.
    """
    db_obj = MaterialPurchase(
        transaction_date=obj_in.transaction_date,
        customer_id=obj_in.customer_id,
        material_type=obj_in.material_type,
        storage_name=obj_in.storage_name,
        trip_count=obj_in.trip_count or 1,
        weight=obj_in.weight or 0.0,
        unit_price=obj_in.unit_price or 0.0,
        total_amount=obj_in.total_amount or 0.0,
        advance_payment=obj_in.advance_payment or 0.0,
        debt=obj_in.debt or 0.0,
        notes=obj_in.notes,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_material_purchase(db: Session, purchase_id: UUID) -> Optional[MaterialPurchase]:
    """
    Delete a material purchase from the database.
    """
    db_obj = db.query(MaterialPurchase).filter(MaterialPurchase.id == purchase_id).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj



def get_inventories(db: Session) -> List[Inventory]:
    """
    Get all inventories from the database.
    """
    return db.query(Inventory).all()


def get_inventories_by_material_name(db: Session, material_name: Optional[str] = None) -> List[Inventory]:
    """
    Get inventories filtered by material_name.
    Supports:
      - Partial match (ILIKE %keyword%): e.g. 'Cao su' matches 'Cao su RSS3'
      - Negation with '!=' prefix: e.g. '!=Cao su' excludes materials containing 'Cao su'
    """
    query = db.query(Inventory)
    if material_name is not None:
        cleaned = material_name.strip().strip("'").strip('"').strip()
        if cleaned.startswith("!="):
            val = cleaned[2:].strip()
            query = query.filter(
                ~Inventory.material_name.ilike(f"%{val}%")
            )
        else:
            query = query.filter(
                Inventory.material_name.ilike(f"%{cleaned}%")
            )
    return query.all()


def create_inventory(db: Session, obj_in) -> Inventory:
    """
    Create a new inventory record in the database.
    """
    db_obj = Inventory(
        material_name=obj_in.material_name,
        quantity=obj_in.quantity or 0.0,
        storage_name=obj_in.storage_name,
        storage_location=obj_in.storage_location,
        capacity=obj_in.capacity or 0.0,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_inventory(db: Session, inventory_id: UUID, obj_in: InventoryUpdate) -> Optional[Inventory]:
    """
    Update an existing inventory record in the database.
    """
    db_obj = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not db_obj:
        return None
    
    update_data = obj_in.dict(exclude_unset=True)
    if "id" in update_data:
        del update_data["id"]
        
    for field, value in update_data.items():
        setattr(db_obj, field, value)
        
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_inventory(db: Session, inventory_id: UUID) -> Optional[Inventory]:
    """
    Delete an inventory record from the database.
    """
    db_obj = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj



def get_inventory_exports(
    db: Session,
    storage_name: Optional[str] = None,
    material_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[InventoryExport]:
    """
    Get all inventory exports, optionally filtered by storage_name, material_type, and date range.
    """
    query = db.query(InventoryExport)
    if storage_name is not None:
        cleaned = storage_name.strip().strip("'").strip('"').strip()
        query = query.filter(InventoryExport.storage_name.ilike(f"%{cleaned}%"))
    if material_type is not None:
        cleaned = material_type.strip().strip("'").strip('"').strip()
        query = query.filter(InventoryExport.material_type.ilike(f"%{cleaned}%"))
    if start_date is not None:
        query = query.filter(InventoryExport.export_date >= start_date)
    if end_date is not None:
        query = query.filter(InventoryExport.export_date <= end_date)
    return query.all()


def get_product_transactions(
    db: Session,
    transaction_type: Optional[str] = None,
    material_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    storage_name: Optional[str] = None,
) -> List[ProductTransaction]:
    """
    Get product transactions optionally filtered by transaction_type, material_type, date range, and storage_name.
    """
    query = db.query(ProductTransaction)
    if transaction_type is not None:
        cleaned = transaction_type.strip().strip("'").strip('"').strip()
        query = query.filter(ProductTransaction.transaction_type.ilike(f"%{cleaned}%"))
    if material_type is not None:
        cleaned = material_type.strip().strip("'").strip('"').strip()
        query = query.filter(ProductTransaction.material_type.ilike(f"%{cleaned}%"))
    if start_date is not None:
        query = query.filter(ProductTransaction.transaction_date >= start_date)
    if end_date is not None:
        query = query.filter(ProductTransaction.transaction_date <= end_date)
    if storage_name is not None:
        cleaned = storage_name.strip().strip("'").strip('"').strip()
        query = query.filter(ProductTransaction.storage_name.ilike(f"%{cleaned}%"))
    return query.all()


def create_product_transaction(db: Session, obj_in, commit: bool = True) -> ProductTransaction:
    """
    Create a new product transaction record in the database.
    """
    db_obj = ProductTransaction(
        product_code=obj_in.product_code,
        transaction_date=obj_in.transaction_date,
        customer_id=obj_in.customer_id,
        transaction_type=obj_in.transaction_type,
        material_type=obj_in.material_type,
        storage_id=obj_in.storage_id,
        storage_name=obj_in.storage_name,
        quantity=obj_in.quantity or 0.0,
        unit_price=obj_in.unit_price or 0.0,
        total_amount=obj_in.total_amount or 0.0,
        debt=obj_in.debt or 0.0,
        note=obj_in.note,
    )
    db.add(db_obj)
    if commit:
        db.commit()
        db.refresh(db_obj)
    else:
        db.flush()
    return db_obj


def delete_product_transaction(db: Session, transaction_id: UUID) -> Optional[ProductTransaction]:
    """
    Delete a product transaction record from the database.
    """
    db_obj = db.query(ProductTransaction).filter(ProductTransaction.id == transaction_id).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj


def create_inventory_export(db: Session, obj_in, remaining_weight: float = 0.0) -> InventoryExport:
    """
    Create a new inventory export record in the database.
    """
    db_obj = InventoryExport(
        export_date=obj_in.export_date,
        performer_name=obj_in.performer_name,
        material_type=obj_in.material_type,
        storage_name=obj_in.storage_name,
        export_weight=obj_in.export_weight or 0.0,
        remaining_weight=remaining_weight,
        notes=obj_in.notes,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_inventory_export(db: Session, export_id: UUID) -> Optional[InventoryExport]:
    """
    Delete an inventory export record from the database.
    """
    db_obj = db.query(InventoryExport).filter(InventoryExport.id == export_id).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj



def get_partners(db: Session) -> List[Partners]:
    """
    Get all partners from the database.
    """
    return db.query(Partners).all()


def create_partner(db: Session, obj_in: PartnerCreate) -> Partners:
    """
    Create a new partner in the database.
    """
    db_obj = Partners(
        partner_id=obj_in.partner_id,
        partner_name=obj_in.partner_name,
        total_debt=obj_in.total_debt,
        username=obj_in.username,
        telegram_group=obj_in.telegram_group,
        bank_name=obj_in.bank_name,
        bank_account=obj_in.bank_account,
        status=obj_in.status
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_partner(db: Session, partner_uuid: UUID, obj_in: PartnerUpdate) -> Optional[Partners]:
    """
    Update an existing partner in the database.
    """
    db_obj = db.query(Partners).filter(Partners.id == partner_uuid).first()
    if not db_obj:
        return None
    
    update_data = obj_in.dict(exclude_unset=True)
    if "id" in update_data:
        del update_data["id"]
        
    for field, value in update_data.items():
        setattr(db_obj, field, value)
        
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_partner(db: Session, partner_uuid: UUID) -> Optional[Partners]:
    """
    Delete a partner from the database.
    """
    db_obj = db.query(Partners).filter(Partners.id == partner_uuid).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj


def get_partner_businesses_detailed(
    db: Session,
    product_type: Optional[str] = None,
    transaction_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[dict]:
    """
    Get all partner businesses joined with Partners to get the partner's partner_name.
    Supports optional filtering by product_type, transaction_type (import/export), and day range.
    """
    query = db.query(
        PartnerBusinesses,
        Partners.partner_name
    ).outerjoin(
        Partners, PartnerBusinesses.partner_id == Partners.partner_id
    )
    
    if start_date is not None:
        query = query.filter(PartnerBusinesses.day >= start_date)
    if end_date is not None:
        query = query.filter(PartnerBusinesses.day <= end_date)
    if product_type is not None:
        cleaned_product_type = product_type.strip()
        query = query.filter(PartnerBusinesses.product_type.ilike(cleaned_product_type))
    if transaction_type is not None:
        cleaned_tx_type = transaction_type.strip().lower()
        if cleaned_tx_type == "import":
            query = query.filter(PartnerBusinesses.import_amount > 0)
        elif cleaned_tx_type == "export":
            query = query.filter(PartnerBusinesses.export_amount > 0)
            
    results = query.all()
    
    data = []
    for pb, partner_name in results:
        data.append({
            "id": pb.id,
            "day": pb.day,
            "partner_id": pb.partner_id,
            "partner_name": partner_name,
            "import_amount": pb.import_amount,
            "export_amount": pb.export_amount,
            "order_code": pb.order_code,
            "unit_price": pb.unit_price,
            "total_amount": pb.total_amount,
            "notes": pb.notes,
            "product_type": pb.product_type,
            "actual_weight": pb.actual_weight,
            "dry_rubber": pb.dry_rubber,
            "degree": pb.degree
        })
    return data



def create_partner_business(db: Session, obj_in: PartnerBusinessCreate) -> PartnerBusinesses:
    """
    Create a new partner business record in the database.
    """
    db_obj = PartnerBusinesses(
        day=obj_in.day,
        partner_id=obj_in.partner_id,
        import_amount=obj_in.import_amount,
        export_amount=obj_in.export_amount,
        order_code=obj_in.order_code,
        unit_price=obj_in.unit_price,
        total_amount=obj_in.total_amount,
        notes=obj_in.notes,
        product_type=obj_in.product_type,
        actual_weight=obj_in.actual_weight,
        dry_rubber=obj_in.dry_rubber,
        degree=obj_in.degree
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_partner_business(db: Session, business_id: UUID, obj_in: PartnerBusinessUpdate) -> Optional[PartnerBusinesses]:
    """
    Update an existing partner business record in the database.
    """
    db_obj = db.query(PartnerBusinesses).filter(PartnerBusinesses.id == business_id).first()
    if not db_obj:
        return None
    
    update_data = obj_in.dict(exclude_unset=True)
    if "id" in update_data:
        del update_data["id"]
        
    for field, value in update_data.items():
        setattr(db_obj, field, value)
        
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_partner_business(db: Session, business_id: UUID) -> Optional[PartnerBusinesses]:
    """
    Delete a partner business record from the database.
    """
    db_obj = db.query(PartnerBusinesses).filter(PartnerBusinesses.id == business_id).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj


def get_investments(
    db: Session,
    role: Optional[str] = None,
    parent_id: Optional[UUID] = None
) -> List[Investment]:
    """
    Get all investments, optionally filtered by role (case-insensitive) and parent_id.
    """
    query = db.query(Investment)
    if role is not None:
        cleaned_role = role.strip()
        query = query.filter(Investment.role.ilike(cleaned_role))
    if parent_id is not None:
        query = query.filter(Investment.parent_id == parent_id)
    return query.all()


def create_investment(db: Session, obj_in: InvestmentCreate) -> Investment:
    """
    Create a new investment in the database.
    """
    db_obj = Investment(
        investment_code=obj_in.investment_code,
        name=obj_in.name,
        initial_capital=obj_in.initial_capital,
        start_date=obj_in.start_date,
        end_date=obj_in.end_date,
        total_income=obj_in.total_income,
        total_expense=obj_in.total_expense,
        profit=obj_in.profit,
        notes=obj_in.notes,
        status=obj_in.status,
        parent_id=obj_in.parent_id,
        role=obj_in.role
    )
    if obj_in.id is not None:
        db_obj.id = obj_in.id
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_investment(db: Session, investment_uuid: UUID, obj_in: InvestmentUpdate) -> Optional[Investment]:
    """
    Update an existing investment in the database.
    """
    db_obj = db.query(Investment).filter(Investment.id == investment_uuid).first()
    if not db_obj:
        return None
    
    update_data = obj_in.dict(exclude_unset=True)
    if "id" in update_data:
        del update_data["id"]
        
    for field, value in update_data.items():
        setattr(db_obj, field, value)
        
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_investment(db: Session, investment_uuid: UUID) -> Optional[Investment]:
    """
    Delete an investment from the database.
    """
    db_obj = db.query(Investment).filter(Investment.id == investment_uuid).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj



def get_daily_payments(
    db: Session,
    investment_id: Optional[UUID] = None,
    payment_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[DailyPayment]:
    """
    Get all daily payments from the database, optionally filtered by investment_id, payment_type, and day range.
    """
    query = db.query(DailyPayment)
    if investment_id is not None:
        query = query.filter(DailyPayment.investment_id == investment_id)
    if payment_type is not None:
        cleaned_type = payment_type.strip()
        query = query.filter(DailyPayment.payment_type.ilike(cleaned_type))
    if start_date is not None:
        query = query.filter(DailyPayment.day >= start_date)
    if end_date is not None:
        query = query.filter(DailyPayment.day <= end_date)
    return query.all()


def create_daily_payment(db: Session, obj_in: DailyPaymentCreate) -> DailyPayment:
    """
    Create a new daily payment record in the database.
    """
    db_obj = DailyPayment(
        investment_id=obj_in.investment_id,
        requester=obj_in.requester,
        executor=obj_in.executor,
        receiver=obj_in.receiver,
        payment_type=obj_in.payment_type,
        purpose=obj_in.purpose,
        reason=obj_in.reason,
        amount=obj_in.amount,
        day=obj_in.day,
        status=obj_in.status,
        notes=obj_in.notes,
        transaction_code=obj_in.transaction_code
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_daily_payment(db: Session, payment_id: UUID) -> Optional[DailyPayment]:
    """
    Delete a daily payment record by its id.
    """
    db_obj = db.query(DailyPayment).filter(DailyPayment.id == payment_id).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj


def update_investment_financials(db: Session, investment_id: UUID, payment_type: str, amount: float):
    """
    Update investment total_income or total_expense based on payment_type,
    then recalculate profit. Also propagate to parent investment if exists.
    
    - payment_type == "thu" → total_income += amount
    - payment_type == "chi" → total_expense += amount
    - profit = total_income - total_expense
    """
    LogInfo(f"[Financials] Starting update: investment_id={investment_id}, payment_type='{payment_type}', amount={amount}")
    
    investment = db.query(Investment).filter(Investment.id == investment_id).first()
    if not investment:
        LogInfo(f"[Financials] Investment {investment_id} NOT FOUND - skipping")
        return

    LogInfo(f"[Financials] Found investment '{investment.investment_code}' - BEFORE: income={investment.total_income}, expense={investment.total_expense}, profit={investment.profit}")

    # Update child investment
    normalized_type = payment_type.strip().lower()
    if normalized_type == "thu":
        investment.total_income = (investment.total_income or 0) + amount
        LogInfo(f"[Financials] payment_type='thu' → total_income += {amount}")
    elif normalized_type == "chi":
        investment.total_expense = (investment.total_expense or 0) + amount
        LogInfo(f"[Financials] payment_type='chi' → total_expense += {amount}")
    else:
        LogInfo(f"[Financials] WARNING: payment_type='{payment_type}' không khớp 'thu' hoặc 'chi' - skipping")
        return

    investment.profit = (investment.total_income or 0) - (investment.total_expense or 0)
    LogInfo(f"[Financials] Investment '{investment.investment_code}' - AFTER: income={investment.total_income}, expense={investment.total_expense}, profit={investment.profit}")

    # Propagate to parent investment (only 2 levels: parent ↔ child)
    if investment.parent_id:
        parent = db.query(Investment).filter(Investment.id == investment.parent_id).first()
        if parent:
            LogInfo(f"[Financials] Propagating to parent '{parent.investment_code}' - BEFORE: income={parent.total_income}, expense={parent.total_expense}, profit={parent.profit}")
            if normalized_type == "thu":
                parent.total_income = (parent.total_income or 0) + amount
            elif normalized_type == "chi":
                parent.total_expense = (parent.total_expense or 0) + amount

            parent.profit = (parent.total_income or 0) - (parent.total_expense or 0)
            LogInfo(f"[Financials] Parent '{parent.investment_code}' - AFTER: income={parent.total_income}, expense={parent.total_expense}, profit={parent.profit}")
        else:
            LogInfo(f"[Financials] Parent investment {investment.parent_id} NOT FOUND")
    else:
        LogInfo(f"[Financials] Investment has no parent_id - no propagation needed")

    db.commit()
    LogInfo(f"[Financials] Committed successfully")
