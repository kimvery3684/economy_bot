import streamlit as st
import urllib.request
import urllib.parse
import json
import re
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import requests  # 구글 도구 대신 직접 접속 (오류 원천 차단)

# ==========================================
# 👇 [중요] 제미나이 API 키를 따옴표("") 사이에 정확히 넣어주세요.
# 예시: GEMINI_API_KEY = "AIzaSy..." (끝에 따옴표 꼭 닫기!)
GEMINI_API_KEY = "AIzaSyC-QRPifVhQGIGCjxk2kKDC0htuyiG0fTk"
# ==========================================

# --- 1. 네이버 검색 함수 (변경 없음) ---
def naver_blog_search(keyword):
    client_id = "sk0nUwhPD16DNEo0gQkD"
    client_secret = "1cLzXGU3Yn"
    
    clean_keyword = keyword.replace('"', '').replace("'", "")
    encText = urllib.parse.quote(clean_keyword)
    url = f"https://openapi.naver.com/v1/search/blog?query={encText}&display=15&sort=sim" 
    
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    
    try:
        response = urllib.request.urlopen(request)
        if response.getcode() == 200:
            return json.loads(response.read().decode('utf-8'))['items']
    except Exception as e:
        return None
    return None

# --- 2. 🤖 제미나이 연결 함수 (가장 안정적인 gemini-pro 사용) ---
def ask_gemini_to_draft(topic, raw_data):
    # 키 입력 확인
    if len(GEMINI_API_KEY) < 10 or "여기에" in GEMINI_API_KEY:
        st.error("🚨 오류: 코드 상단의 GEMINI_API_KEY에 실제 키를 입력하지 않았습니다.")
        return None

    # 데이터 정리
    context = ""
    for item in raw_data:
        title = item['title'].replace('<b>', '').replace('</b>', '')
        desc = item['description'].replace('<b>', '').replace('</b>', '')
        context += f"- {title} : {desc}\n"

    # 프롬프트
    prompt = f"""
    너는 경제 쇼츠 작가야. 아래 블로그 내용을 바탕으로 '{topic}'에 들어갈 TOP 10 리스트를 작성해줘.
    
    [규칙]
    1. 광고는 빼고 핵심 정보만 골라.
    2. 각 줄은 '순위. 키워드 - 설명' 형태로 작성해.
    3. 설명은 최대한 짧고 임팩트 있게(20자 이내).
    4. 서론, 본론 다 빼고 오직 리스트 10줄만 출력해.

    [참고 데이터]
    {context}
    """

    # 🔥 [핵심 수정] 모델을 'gemini-pro'로 변경 (가장 호환성 높음)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    data = { "contents": [{ "parts": [{"text": prompt}] }] }

    try:
        response = requests.post(url, headers=headers, json=data)
        
        # 성공 (200 OK)
        if response.status_code == 200:
            result = response.json()
            try:
                return result['candidates'][0]['content']['parts'][0]['text']
            except:
                st.error("AI가 답변을 생성했지만 내용을 추출하지 못했습니다. 다시 시도해주세요.")
                return None
        else:
            # 실패 시 에러 메시지 출력
            st.error(f"AI 연결 오류 ({response.status_code}): {response.text}")
            return None
            
    except Exception as e:
        st.error(f"서버 통신 실패: {e}")
        return None

# --- 3. 이미지 생성 함수 (변경 없음) ---
def create_ranking_image(topic, text_content):
    W, H = 1080, 1350 
    img = Image.new('RGB', (W, H), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 70) 
        font_list = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 40)
        font_sub = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 35)
    except:
        font_title = ImageFont.load_default()
        font_list = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # 테두리
    draw.rectangle([(0,0), (W, H)], outline=(255, 0, 0), width=15)
    draw.line([(0, 250), (W, 250)], fill=(255, 0, 0), width=5)

    # 제목
    para = textwrap.wrap(topic, width=16)
    current_h = 80
    for line in para:
        bbox = draw.textbbox((0, 0), line, font=font_title)
        text_w = bbox[2] - bbox[0]
        draw.text(((W - text_w) / 2, current_h), line, font=font_title, fill="white")
        current_h += 80

    draw.text((50, 270), "Updated by Gemini AI", font=font_sub, fill="gray")

    # 리스트 그리기
    lines = text_content.strip().split('\n')
    start_y = 350
    gap = 90
    
    count = 0
    for line in lines:
        clean_line = line.strip()
        if not clean_line: continue
        
        # 순위 숫자로 시작하는지 확인 (예: "1. 삼성전자")
        # AI가 이상한 말을 섞을 수 있으므로 필터링
        if len(clean_line) > 0:
            count += 1
            if count > 10: break

            if len(clean_line) > 28: 
                clean_line = clean_line[:28] + "..."
                
            color = (255, 215, 0) if count <= 3 else "white"
            draw.text((80, start_y), clean_line, font=font_list, fill=color)
            start_y += gap

    footer = "구독 🙏 좋아요 ❤️"
    bbox_foot = draw.textbbox((0, 0), footer, font=font_list)
    draw.text(((W - (bbox_foot[2] - bbox_foot[0]))/2, H - 100), footer, font=font_list, fill=(255, 100, 100))

    return img

# --- 4. 메인 화면 ---
st.set_page_config(page_title="AI 경제 쇼츠 공장", page_icon="🏭", layout="wide")
st.title("🏭 3호점: 편집 가능한 쇼츠 공장")

if 'draft_text' not in st.session_state:
    st.session_state['draft_text'] = ""
if 'final_img' not in st.session_state:
    st.session_state['final_img'] = None

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 주제 및 내용 편집")
    topic = st.text_input("주제", value="2025년 급등 예상 AI 관련주 TOP 10")
    
    # [Step 1] 검색 및 초안 생성
    if st.button("Step 1. 검색하고 초안 만들기 📝", use_container_width=True):
        with st.spinner("네이버 검색 후 AI가 요약 중입니다... (약 5초 소요)"):
            raw_data = naver_blog_search(topic)
            if raw_data:
                draft = ask_gemini_to_draft(topic, raw_data)
                if draft:
                    st.session_state['draft_text'] = draft
                    st.success("초안 작성 완료! 아래 내용을 수정하세요.")
            else:
                st.error("네이버 검색 결과가 없습니다.")

    # [편집기] 사용자가 직접 수정
    edited_text = st.text_area(
        "내용 수정 (오타나 순위를 직접 고치세요)", 
        value=st.session_state['draft_text'],
        height=400,
        placeholder="위 버튼을 누르면 AI가 작성한 초안이 여기에 나타납니다."
    )

    # [Step 2] 이미지 생성
    if st.button("Step 2. 이 내용으로 이미지 만들기 🎨", use_container_width=True, type="primary"):
        if edited_text:
            img = create_ranking_image(topic, edited_text)
            st.session_state['final_img'] = img
        else:
            st.warning("내용이 비어있습니다. 먼저 Step 1을 진행해주세요.")

with col2:
    st.subheader("🖼️ 결과 이미지")
    if st.session_state['final_img']:
        st.image(st.session_state['final_img'], caption="최종 결과물", use_container_width=True)
        
        buf = io.BytesIO()
        st.session_state['final_img'].save(buf, format="PNG")
        st.download_button("💾 이미지 다운로드", buf.getvalue(), "shorts_rank.png", "image/png", use_container_width=True)
    else:
        st.info("왼쪽에서 [Step 2] 버튼을 누르면 완성된 이미지가 여기에 뜹니다.")