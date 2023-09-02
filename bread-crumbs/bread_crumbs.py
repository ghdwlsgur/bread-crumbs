from typing import List
from flask_restx import Resource, Namespace
from .bread_crumbs_api_models import res_model
from . import config
import uuid 
import pymysql 


class Node:
  def __init__(self, id: str, title: str, content: str):
    self.id = id 
    self.title = title # 제목 
    self.content = content # 내용 
    self.sub_page = [] # 서브 페이지 목록 
    self.parent_page = None # 부모 페이지 
  
  def add_sub_page(self, page):
    page.parent_page = self # 서브 페이지의 부모 페이지를 이 노드로 지정 
    self.sub_page.append(page) # 이 노드의 서브 페이지에 추가
  
  
class Tree:
  def __init__(self):
    self.nodes = {}
    
  def get_node(self, id) -> str:
    if id in self.nodes:
      return self.nodes[id]
  
  def create_node(self, id: str, title: str, content: str) -> str: 
    if id not in self.nodes:
      self.nodes[id] = Node(id, title, content)
    return self.nodes[id]
  
  def connect_node(self, parent_page_id, sub_page_id):
    if parent_page_id in self.nodes and sub_page_id in self.nodes:
      self.nodes[parent_page_id].add_sub_page(self.nodes[sub_page_id])
  
  def get_breadcrumbs(self, node):
    path = []
    while node:
      path.append(node)
      node = node.parent_page 
    
    return path[::-1]
    

class Database:
  @staticmethod 
  def get_connection(config):
    connection = pymysql.connect(
        user=config.db['user'],
        password=config.db['password'],
        host=config.db['host'],
        port=config.db['port'],
        db=config.db['database'],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

class ResponseData: 
  def __init__(self, statusCode: int, id: str, title: str, content: str, sub_page: List, bread_crumbs: List):
    self.statusCode = statusCode 
    self.id = id 
    self.title = title 
    self.content = content 
    self.sub_page = sub_page 
    self.bread_crumbs = bread_crumbs 
    
  def to_dict(self):
    return {
      'statusCode': self.statusCode, 
      'id': self.id, 
      'title': self.title, 
      'content': self.content, 
      'sub_page': self.sub_page, 
      'bread_crumbs': self.bread_crumbs
    }




ns = Namespace("page")

@ns.route("/<string:id>")
@ns.doc(params={'id': '페이지 아이디'})
class GetPage(Resource):
  @ns.doc(response={
    200: 'Success',
    404: 'Page Not Found'
  })
  @ns.marshal_with(res_model)
  @ns.doc(description="페이지를 조회합니다.")
  def get(self, id) -> ResponseData:    
    conn = None 
    tree = Tree()
    
    try: 
      conn = Database.get_connection(config)
      with conn.cursor() as cursor:
        query = """
        SELECT id, title, content, parent_page_id FROM PAGE        
        """
        cursor.execute(query)
        page_list = cursor.fetchall()
        
        for page in page_list:
          page_id = page['id']
          title = page['title']
          content = page['content']          
          tree.create_node(page_id, title, content)
        
        for page in page_list: 
          page_id = page['id']
          parent_page_id = page['parent_page_id']
          if parent_page_id:
            tree.connect_node(parent_page_id, page_id)
            
      curr_node = tree.get_node(id)
      if not curr_node:        
        response_data = ResponseData(404, None, None, None, None, None)
        return response_data.to_dict(), 404    
      
      bread_crumbs = [node.id for node in tree.get_breadcrumbs(curr_node)]      
      sub_pages = [sub_page.id for sub_page in curr_node.sub_page]
      
      response_data = ResponseData(200, curr_node.id, curr_node.title, curr_node.content, sub_pages, bread_crumbs)
      return response_data.to_dict(), 200 
            
    except Exception as e:
      return e 
    finally:
      if conn: 
        conn.close()
                      
  
@ns.route("")
class CreatePage(Resource):
  @ns.doc(responses={
    200: 'Success'
  })    
  @ns.doc(description="테스트 데이터 저장")
  def post(self) -> ResponseData:
    # 5 -> 4 -> 2, 3 
    datas = [
      {"id": 1, "title": "Title1", "content": "Content1", "parent_page_id": None},
      {"id": 2, "title": "Title1", "content": "Content1", "parent_page_id": 4},      
      {"id": 3, "title": "Title1", "content": "Content1", "parent_page_id": 4},
      {"id": 4, "title": "Title1", "content": "Content1", "parent_page_id": 5},
      {"id": 5, "title": "Title1", "content": "Content1", "parent_page_id": None},
    ]    
    
    conn = None
    try:
      conn = Database.get_connection(config)
      with conn.cursor() as cursor:                      
        for data in datas:
          query = """
          INSERT INTO PAGE (id, title, content, parent_page_id)
          VALUES (%s, %s, %s, %s)      
          """                
          cursor.execute(query, (data["id"], data["title"], data["content"], data["parent_page_id"]))        
        conn.commit()                                     
      return 200
    except Exception as e:
      if conn:
        conn.rollback()        
      print(str(e))
    finally:
      if conn:
        conn.close()    
            
    

    