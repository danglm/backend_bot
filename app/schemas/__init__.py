from .auth import UserRegister, UserLogin, Token, ForgotPassword
from .project import ProjectBase, ProjectCreate, Project
from .customer import CustomerResponse, CustomerCreate
from .collection_point import CollectionPointResponse
from .daily_purchase import DailyPurchaseResponse, DailyPurchaseCreate, DailyPurchaseUpdate
from .material_purchase import MaterialPurchaseResponse, MaterialPurchaseCreate
from .inventory import InventoryResponse, InventoryCreate, InventoryUpdate
from .partner import PartnerResponse, PartnerCreate, PartnerUpdate
from .partner_business import PartnerBusinessResponse, PartnerBusinessCreate, PartnerBusinessUpdate
from .investment import InvestmentResponse, InvestmentCreate, InvestmentUpdate
from .daily_payment import DailyPaymentResponse, DailyPaymentCreate
from .inventory_export import InventoryExportResponse, InventoryExportCreate
from .product_transaction import ProductTransactionResponse, ProductTransactionCreate
from .payroll import PayrollResponse, PayrollCreate
from .loss_control import ProcessLossControlRequest, LossControlItem, ProcessLossControlResponse


