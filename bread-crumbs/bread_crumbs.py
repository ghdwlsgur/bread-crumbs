from typing import List
from flask_restx import Resource, Namespace
from .bread_crumbs_api_models import res_model
from . import config
import pymysql 


class Node:
  def __init__(self, id: str, title: str, content: str):
    self.id = id 
    self.title = title # 제목 
    self.content = content # 내용 
    self.sub_page = [] # 서브 페이지 목록 
    self.parent_page = None # 부모 페이지 Node: Node
  
  def add_sub_page(self, page):
    page.parent_page = self # 서브 페이지의 부모 페이지를 이 노드로 지정 
    self.sub_page.append(page) # 이 노드의 서브 페이지에 추가
  
  
class Tree:
  def __init__(self):
    # 아이디를 키로 갖고 노드를 밸류로 갖는 nodes 인스턴스 변수 생성 
    self.nodes = {}
    
  # 트리가 가진 노드들 중 인수 아이디와 동일한 아이디를 가진 노드 반환
  def get_node(self, id) -> str:
    if id in self.nodes:
      return self.nodes[id]
  
  # 신규 노드 생성 
  def create_node(self, id: str, title: str, content: str): 
    # 현재 동일한 아이디를 가진 노드가 존재하지 않을 경우 노드 생성
    if id not in self.nodes:
      self.nodes[id] = Node(id, title, content)
    
  # 부모 페이지 노드와 자식 노드 페이지를 서로 연결
  def connect_node(self, parent_page_id: str, sub_page_id: str):
    # 노드에 부모 페이지 아이디와 서브 페이지 아이디가 존재할 경우 서로 연결    
    if parent_page_id in self.nodes and sub_page_id in self.nodes:
      self.nodes[parent_page_id].add_sub_page(self.nodes[sub_page_id])
  
  # breadcrumbs 가져오기 
  def get_breadcrumbs(self, node: Node):
    # path 변수에 빈 리스트 할당 
    path = []
    # 현재 노드부터 부모 페이지 노드까지 거슬러서 순회 
    while node:
      path.append(node)
      node = node.parent_page 
    
    # 리스트에 현재 노드부터 추가되기 때문에 역순하여 반환 
    return path[::-1]
    

# 데이터베이스 연결
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

# 응답 데이터 형식 
class ResponseData: 
  def __init__(self, id: str, title: str, content: str, sub_page: List, bread_crumbs: List):
    # self.statusCode = statusCode 
    self.id = id 
    self.title = title 
    self.content = content 
    self.sub_page = sub_page 
    self.bread_crumbs = bread_crumbs 
    
  def to_dict(self):
    return {
      # 'statusCode': self.statusCode, # 상태코드 
      'id': self.id, # 페이지 아이디 
      'title': self.title, # 페이지 제목
      'content': self.content, # 페이지 내용
      'sub_page': self.sub_page, # 서브 페이지 목록
      'bread_crumbs': self.bread_crumbs # 페이지 경로
    }

ns = Namespace("page")

@ns.route("/<string:id>")
@ns.doc(params={'id': '페이지 아이디'})
class GetPage(Resource):
  @ns.doc(response={
    200: 'Success',
    404: 'Page Not Found', 
    503: "Interner Server Error"
  })
  @ns.marshal_with(res_model)
  @ns.doc(description="페이지를 조회합니다.")
  def get(self, id: str) -> ResponseData:    
    conn = None 
    tree = Tree()
    
    try: 
      conn = Database.get_connection(config)
      with conn.cursor() as cursor:
        query = """
        SELECT id, title, content, parent_page_id FROM PAGE        
        """
        cursor.execute(query) # 쿼리 실행 
        page_list = cursor.fetchall() # 전체 페이지 테이블 조회 결과 page_list에 저장 
        
        # 1. page_list를 순회하면서 각 row마다 Node 생성
        for page in page_list:
          page_id = page['id']
          title = page['title']
          content = page['content']          
          tree.create_node(page_id, title, content)
        
        # 2. 현재 페이지에 부모 페이지가 존재할 경우 현재 페이지 노드와 부모 페이지 노드를 서로 연결
        for page in page_list: 
          page_id = page['id']
          parent_page_id = page['parent_page_id']
          if parent_page_id:
            tree.connect_node(parent_page_id, page_id)
            
      # 현재 조회하려는 노드를 변수에 저장             
      curr_node = tree.get_node(id)
      # 만약 현재 조회하려는 노드가 존재하지 않는다면 404
      if not curr_node:        
        response_data = ResponseData(None, None, None, None, None)
        return response_data.to_dict(), 404    
      
      bread_crumbs = [node.id for node in tree.get_breadcrumbs(curr_node)]      
      sub_pages = [sub_page.id for sub_page in curr_node.sub_page]
      
      response_data = ResponseData(curr_node.id, curr_node.title, curr_node.content, sub_pages, bread_crumbs)
      return response_data.to_dict(), 200
            
    except Exception as e:
      response_data = ResponseData(None, None, None, None, None)
      return response_data.to_dict(), 500
    finally:
      if conn: 
        conn.close()
                      
  
@ns.route("")
class CreatePage(Resource):
  @ns.doc(responses={
    200: 'Success'
  })    
  @ns.doc(description="테스트 케이스 데이터 저장합니다.")
  def post(self) -> int:
    # 5 -> 4, 1 -> 2, 3 
    datas = [
      {"id": 5, "title": "Title1", "content": "Content1", "parent_page_id": None},
      {"id": 4, "title": "Title1", "content": "Content1", "parent_page_id": 5},      
      {"id": 1, "title": "Title1", "content": "Content1", "parent_page_id": 5},      
      {"id": 2, "title": "Title1", "content": "Content1", "parent_page_id": 4},      
      {"id": 3, "title": "Title1", "content": "Content1", "parent_page_id": 4},                  
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
    finally:
      if conn:
        conn.close()    
            
    

    