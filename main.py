import logging
import uuid
from fastapi import FastAPI, File, Request, status, HTTPException
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

log = logging.getLogger('uvicorn')


class ImageTemplate(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    template_name: str = Field(...)
    encoded_image: bytes = File(...)

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "id": "00010203-0405-0607-0809-0a0b0c0d0e0f",
                "template_name": "Template ABC",
                "encoded_image": "Image in base64"
            }
        }


app = FastAPI()


@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient('mongodb://localhost:27017')
    app.mongodb = app.mongodb_client['docs']


@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()


@app.post('/register')
async def register(request: Request, newTemplate: ImageTemplate):
    task = jsonable_encoder(newTemplate)
    new_task = await request.app.mongodb["receipts"].insert_one(task)
    log.info('Template Name {}, With Id {} Successfully Registered'.format(newTemplate.template_name, new_task.inserted_id))
    return JSONResponse(status_code=status.HTTP_201_CREATED,content=new_task.inserted_id)

@app.post('/view')
async def view(request: Request, template_name: str):
    if (task := await request.app.mongodb["receipts"].find_one({"template_name": template_name})) is not None: 
        return task
    raise HTTPException(status_code=404, detail=f"Template {template_name} not found")