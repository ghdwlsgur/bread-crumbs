from flask_restx import fields 
from .extensions import api 

req_model = api.model("CreatePage", {
  "title": fields.String(description='제목', required=True),
  "content": fields.String(description='내용', required=True),
  "parent_page_id": fields.String(description='부모 페이지 아이디', required=False)  
})
