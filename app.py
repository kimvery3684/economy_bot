import streamlit as st
import urllib.request
import urllib.parse
import json
import re

# --- 1. HTML 태그 제거 및 텍스트 정리 함수 ---
def clean_html(text):
    """<b>, &quot; 같은 지저분한 태그를 제거하는 함수"""
    text = re.sub('<.*?>', '', text) # 태그 제거
    text = text.replace('&quot;', '"').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    return text

# --- 2. 네이버 검색 함수 ---
def naver_blog_search(keyword):
    client_id = "sk0nUwhPD16DNEo0gQkD"
    client_secret = "1cLzXGU3Yn"
    
    encText = urllib.parse.quote(keyword)
    url = "https://openapi.naver.com/v1/search/blog?query=" + encText + "&display=10" # 10개 검색
    
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    
    try:
        response = urllib.request.urlopen(request)
        if response.getcode() == 200:
            response_body = response.read()
            data = json.loads(response_body.decode('utf-8'))
            return data['items']
        else:
            return None
    except Exception as e:
        st.error(f"검색 중 오류 발생: {e}")
        return None

# --- 3. Streamlit 화면 구성 ---
st.set_page_config(page_title="경제 쇼츠 자동 공장", page_icon="💰", layout="wide")

st.title("💰 3호점: 경제 쇼츠 자동 완성 공장")

# 세션 상태 초기화
if 'search_result' not in st.session_state:
    st.session_state['search_result'] = ""
if 'current_topic' not in st.session_state:
    st.session_state['current_topic'] = "2025년 급등 예상 저평가 우량주 TOP 10"

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 콘텐츠 자동 생성")
    
    with st.container(border=True):
        # 버튼 클릭 시 동작
        if st.button("🔍 주제 검색 & AI 프롬프트 생성", use_container_width=True):
            target_keyword = st.session_state['current_topic']
            
            with st.spinner(f"네이버에서 '{target_keyword}' 정보를 긁어오는 중..."):
                items = naver_blog_search(target_keyword)
                
                if items:
                    # 1. 수집된 데이터 정리 (사람이 보기 좋게)
                    raw_data = f"=== '{target_keyword}' 관련 네이버 블로그 데이터 ===\n\n"
                    for i, item in enumerate(items, 1):
                        title = clean_html(item['title'])
                        desc = clean_html(item['description'])
                        raw_data += f"{i}. 제목: {title}\n   요약: {desc}\n   링크: {item['link']}\n\n"
                    
                    # 2. AI에게 명령할 프롬프트 자동 생성 (여기가 핵심!)
                    ai_prompt = f"""
==================================================
[AI 작업 지시서]
위의 '네이버 블로그 데이터'를 바탕으로 유튜브 쇼츠 대본을 작성해줘.

1. 주제: {target_keyword}
2. 형식: 사람들이 한눈에 볼 수 있는 '랭킹' 또는 '표' 형태
3. 요구사항:
   - 블로그 내용들에서 공통적으로 언급되는 종목이나 트렌드를 5~7개 뽑아줘.
   - 각 항목별로 [순위 / 이름 / 핵심특징 / 수익률(있으면)] 형태로 정리해줘.
   - 결론은 "구독과 좋아요"를 유도하는 멘트로 끝내줘.
   - 말투는 빠르고 임팩트 있게 (유튜브 쇼츠 스타일)
==================================================
"""
                    # 결과 합치기
                    final_output = raw_data + ai_prompt
                    
                    st.session_state['search_result'] = final_output
                    st.success("데이터 수집 완료! 아래 내용을 복사해서 AI에게 붙여넣으세요.")
                else:
                    st.warning("검색 결과가 없습니다.")

        # 제목 입력
        title_input = st.text_area("제목 (여기에 주제를 적으세요)", value=st.session_state['current_topic'], height=68)
        st.session_state['current_topic'] = title_input

        # 데이터 출력
        st.text_area(
            "데이터 & 프롬프트 (복사해서 챗GPT/Gemini에 붙여넣기)", 
            value=st.session_state['search_result'], 
            height=500,
            help="이 내용을 복사해서 AI 채팅창에 그대로 붙여넣으면 바로 대본이 나옵니다."
        )

    with st.expander("디자인 조절"):
        st.write("폰트 크기, 배경 색상 등 설정")

with col2:
    st.subheader("🖼️ 미리보기 & 영상 제작")
    st.info("이곳에 만들어진 랭킹 표 이미지가 표시됩니다.")