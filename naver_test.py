import urllib.request
import urllib.parse
import json

def naver_blog_search(keyword):
    """
    네이버 블로그 검색 API를 호출하는 함수
    :param keyword: 검색할 단어 (문자열)
    :return: 검색 결과 리스트 (제목, 링크 등)
    """
    
    # 1. 인증 정보 설정 (제공해주신 키 입력됨)
    client_id = "sk0nUwhPD16DNEo0gQkD"
    client_secret = "1cLzXGU3Yn"
    
    # 2. URL 및 파라미터 설정
    encText = urllib.parse.quote(keyword)
    url = "https://openapi.naver.com/v1/search/blog?query=" + encText # JSON 결과
    
    # 3. 요청 헤더 생성
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    
    # 4. API 요청 및 응답 처리
    try:
        response = urllib.request.urlopen(request)
        rescode = response.getcode()
        
        if rescode == 200:
            response_body = response.read()
            data = json.loads(response_body.decode('utf-8'))
            return data['items'] # 검색 결과 중 'items' 항목만 반환
        else:
            print("Error Code:" + rescode)
            return None

    except Exception as e:
        print(f"오류 발생: {e}")
        return None

# --- 실행부 ---
if __name__ == "__main__":
    # 검색하고 싶은 키워드 입력
    search_keyword = "파이썬 코딩"
    
    results = naver_blog_search(search_keyword)

    if results:
        print(f"== '{search_keyword}' 검색 결과 (상위 5개) ==")
        for i, item in enumerate(results[:5], 1):
            # HTML 태그 제거 및 출력 깔끔하게 정리
            title = item['title'].replace('<b>', '').replace('</b>', '')
            link = item['link']
            print(f"[{i}] {title}\n    -> 링크: {link}")
    else:
        print("검색 결과가 없습니다.")