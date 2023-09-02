from flask_restx import fields 
from .extensions import api 

 
res_model = api.model("ResponseModel", {
  "id": fields.String, 
  "title": fields.String, 
  "content": fields.String, 
  "sub_page": fields.List(fields.String), 
  "bread_crumbs": fields.List(fields.String),  
})