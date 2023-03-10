from fastapi import FastAPI, Request

from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools import Logger

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer, idempotent, idempotent_function
)

from aws_lambda_powertools.utilities.feature_flags import FeatureFlags, AppConfigStore

app = FastAPI()
logger = Logger(service="demo_container")

# PARAMETER
@app.get("/get_parameters/")
async def get_parameters() -> dict[str, str]:
    logger.info("Getting parameters")
    value_parameter: str = parameters.get_parameter("/lambda-powertools/container")
    return {"parameter_value": value_parameter}

# IDEMPOTENCY
persistence_layer = DynamoDBPersistenceLayer(table_name="ddbtimeout")
@idempotent_function(data_keyword_argument="order_id", persistence_store=persistence_layer)
def proccess_order(order_id: str):
    logger.info((f"Processing order_id {order_id}"))
    return f"processed order {order_id}"

@app.post("/idempotency/")
async def idempotency(request: Request) -> dict[str, str]:
    logger.info("Idempotent function")
    """
    POST body:
    {
        "order":{
            "id": 1
        }
    }
    """
    request_body = await request.json()
    order_id = proccess_order(order_id=request_body.get("order").get("id"))
    return {"message": order_id}

# FEATURE FLAGS
app_config = AppConfigStore(
    environment="dev",
    application="comments",
    name="features"
)

feature_flags = FeatureFlags(store=app_config)
@app.post("/feature_flag/")
async def feature_flag(request: Request) -> dict[str, str]:
    """
    POST body:
    {
        "tenant_id": "xyz"
    }
    """
    logger.info("Feature Flags function")
    request_body = await request.json()
    ctx = {"tenant_id": request_body.get("tenant_id")}
    is_tenant_enabled = feature_flags.evaluate(name="tenant_enabled", context=ctx, default=False)
    if is_tenant_enabled:
        return {"message": "Tenant Enabled"}
    else:
        return {"message": "Tenant Disabled"}


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}
