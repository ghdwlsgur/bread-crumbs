### [팀 과제] 노션에서 브로드 크럼스 만들기 with Python

## 목표

노션과 유사한 간단한 페이지 관리 API를 구현해주세요. 각 페이지는 제목, 컨텐츠, 그리고 서브 페이지를 가질 수 있습니다. 또한, 특정 페이지에 대한 브로드 크럼스(Breadcrumbs) 정보도 반환해야 합니다.

## 요구사항

**페이지 정보 조회 API**: 특정 페이지의 정보를 조회할 수 있는 API를 구현하세요.

- 입력: 페이지 ID
- 출력: 페이지 제목, 컨텐츠, 서브 페이지 리스트, **브로드 크럼스 ( 페이지 1 > 페이지 3 > 페이지 5)**
- 컨텐츠 내에서 서브페이지 위치 고려 X\_

## 제출 방법 (팀단위)

- **과제 내용을 노션 혹은 github 등에 문서화해서 제출해주세요. (마감 9월 5일 오전 10시)**
- **필수**
  - 테이블 구조
  - 비지니스 로직 (Raw 쿼리로 구현 → ORM (X))
  - 결과 정보
    ```java
    {
    		"pageId" : 1,
    		"title" : 1,
    		"subPages" : [],
    		"breadcrumbs" : ["A", "B", "C",] // 혹은 "breadcrumbs" : "A / B / C"
    }
    ```
- 제출하신 과제에 대해서 설명해주세요. (”왜 이 구조가 최선인지?” 등)

---

### 테이블 구조

<div style="display: flex; justify-content: center;">
  <img width="226" alt="스크린샷 2023-09-02 오후 2 26 33" src="https://github.com/petit-a-petit/bread-crumbs/assets/77400522/9076572e-29fa-4220-aad9-920b9dd488d1">  
</div>

```SQL
CREATE TABLE PAGE (
	id VARCHAR(255) PRIMARY KEY,
	title TEXT NOT NULL,
	content TEXT,
	parent_page_id VARCHAR(255),
	FOREIGN KEY (parent_page_id) REFERENCES PAGE(id)
);
```

### 비즈니스 로직

```python
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

        # 모든 페이지 노드 생성
        for page in page_list:
          page_id = page['id']
          title = page['title']
          content = page['content']
          tree.create_node(page_id, title, content)

        # 생성한 노드 중 부모 노드와 자식 노드 연결
        for page in page_list:
          page_id = page['id']
          parent_page_id = page['parent_page_id']
          if parent_page_id:
            tree.connect_node(parent_page_id, page_id)

      # 현재 노드 할당
      curr_node = tree.get_node(id)
      # 현재 노드가 존재하지 않을 경우 404 반환
      if not curr_node:
        response_data = ResponseData(404, None, None, None, None, None)
        return response_data.to_dict(), 404

      # 현재 노드의 브레드크럼브 가져오기
      bread_crumbs = [node.id for node in tree.get_breadcrumbs(curr_node)]
      # 현재 노드의 서브 페이지 가져오기
      sub_pages = [sub_page.id for sub_page in curr_node.sub_page]

      response_data = ResponseData(200, curr_node.id, curr_node.title, curr_node.content, sub_pages, bread_crumbs)
      return response_data.to_dict(), 200

    except Exception as e:
      return e
    finally:
      if conn:
        conn.close()
```

### Response Data

```bash
{
  "statusCode": 200,
  "id": "0e59afa1-e3e2-4b7f-9c32-e121ce7bb782",
  "title": "string",
  "content": "string",
  "sub_page": [
    "782582c8-bd6e-4482-bbf5-2dba7d9c97f2",
    "7fc99a5e-bb1a-4d2a-8aeb-403fcc5d02cb"
  ],
  "bread_crumbs": [
    "0e59afa1-e3e2-4b7f-9c32-e121ce7bb782"
  ]
}
```
