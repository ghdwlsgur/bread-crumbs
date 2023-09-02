from typing import List
from flask_restx import Resource, Namespace, reqparse
from .bread_crumbs_api_models import req_model
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


parser = reqparse.RequestParser()    
parser.add_argument('title', type=str, required=True)
parser.add_argument('content', type=str, required=True)
parser.add_argument('parent_page_id', type=str, required=False)
ns = Namespace("page")

@ns.route("/<string:id>")
@ns.doc(params={'id': '페이지 아이디'})
class GetPage(Resource):
  @ns.doc(response={
    200: 'Success',
    404: 'Page Not Found'
  })
  @ns.doc(description="페이지를 조회합니다.")
  def get(self, id):    
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
          parent_page_id = page['parent_page_id']
          
          tree.create_node(page_id, title, content)
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
  @ns.expect(req_model)
  @ns.doc(description="페이지를 생성합니다.")
  def post(self):
    args = parser.parse_args()
    id: str = uuid.uuid4()
    title: str = args.get('title')
    content: str = args.get('content')       
    parent_page_id = args.get('parent_page_id', None)         

    conn = None
    try:
      conn = Database.get_connection(config)
      with conn.cursor() as cursor:              
        query = """
        INSERT INTO PAGE (id, title, content, parent_page_id)
        VALUES (%s, %s, %s, %s)      
        """        
        cursor.execute(query, (id, title, content, parent_page_id))
        conn.commit()      
    except Exception as e:
      if conn:
        conn.rollback()
    finally:
      if conn:
        conn.close()    
            
    

    