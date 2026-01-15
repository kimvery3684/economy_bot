import streamlit as st
import urllib.request
import urllib.parse
import json
import re
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import requests  # <-- 구글 공식 도구 대신 '직접 접속' 방식을 사용하여 오류 원천 차단

# ==========================================
# 👇 여기에 제미나이 API 키를 입력하세요! (따옴표 닫기 필수!)
GEMINI_API_KEY = "AIzaSyC-QRPifVhQGIGCjxk2kKDC0htuyiG0fTk"
# ==========================================

# --- 1. 네이버 검색 함수 ---
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

# --- 2. 🤖 제미나이 연결 함수 (REST API 방식 - 404 오류 해결책) ---
def ask_gemini_to_draft(topic, raw_data):
    if len(GEMINI_API_KEY) < 10 or "여기에" in GEMINI_API_KEY:
        st.error("⚠️ 코드 상단의 GEMINI_API_KEY에 실제 키를 입력해주세요!")
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
    3. 설명은 최대한 짧고 임팩트 있게.
    4. 오직 리스트 10줄만 출력해. (인사말 금지)

    [참고 데이터]
    {context}
    """

    # 🔥 [핵심] 라이브러리 없이 웹 주소로 직접 요청 (버전 문제 해결)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    data = { "contents": [{ "parts": [{"text": prompt}] }] }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            st.error(f"AI 응답 오류: {response.text}")
            return None
    except Exception as e:
        st.error(f"연결 실패: {e}")
        return None

# --- 3. 이미지 생성 함수 ---
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

    # 리스트 그리기 (텍스트 박스 내용을 줄별로 나눔)
    lines = text_content.strip().split('\n')
    start_y = 350
    gap = 90
    
    for i, line in enumerate(lines[:10], 1): # 최대 10줄
        clean_line = line.strip()
        if not clean_line: continue

        # 글자가 너무 길면 자르기
        if len(clean_line) > 28: 
            clean_line = clean_line[:28] + "..."
            
        color = (255, 215, 0) if i <= 3 else "white"
        draw.text((80, start_y), clean_line, font=font_list, fill=color)
        start_y += gap

    footer = "구독 🙏 좋아요 ❤️"
    bbox_foot = draw.textbbox((0, 0), footer, font=font_list)
    draw.text(((W - (bbox_foot[2] - bbox_foot[0]))/2, H - 100), footer, font=font_list, fill=(255, 100, 100))

    return img

# --- 4. 메인 화면 구성 ---
st.set_page_config(page_title="AI 경제 쇼츠 공장", page_icon="🏭", layout="wide")
st.title("🏭 3호점: 편집 가능한 쇼츠 공장")

# 데이터 저장소 초기화
if 'draft_text' not in st.session_state:
    st.session_state['draft_text'] = ""
if 'final_img' not in st.session_state:
    st.session_state['final_img'] = None

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 주제 및 내용 편집")
    topic = st.text_input("주제", value="2025년 급등 예상 AI 관련주 TOP 10")
    
    # 1단계 버튼: 초안 생성
    if st.button("Step 1. 검색하고 초안 만들기 📝", use_container_width=True):
        with st.spinner("네이버와 제미나이가 자료를 조사 중입니다..."):
            raw_data = naver_blog_search(topic)
            if raw_data:
                draft = ask_gemini_to_draft(topic, raw_data)
                if draft:
                    st.session_state['draft_text'] = draft
                    st.success("초안이 작성되었습니다! 아래에서 수정하세요.")
            else:
                st.error("검색 결과가 없습니다.")

    # 텍스트 편집기 (사용자가 직접 수정 가능)
    edited_text = st.text_area(
        "내용 수정 (여기서 고치면 이미지에 반영됩니다)", 
        value=st.session_state['draft_text'],
        height=400,
        placeholder="버튼을 누르면 여기에 AI가 작성한 초안이 뜹니다."
    )

    # 2단계 버튼: 이미지 생성
    if st.button("Step 2. 이 내용으로 이미지 만들기 🎨", use_container_width=True, type="primary"):
        if edited_text:
            img = create_ranking_image(topic, edited_text)
            st.session_state['final_img'] = img
        else:
            st.warning("먼저 내용을 작성하거나 Step 1 버튼을 눌러주세요.")

with col2:
    st.subheader("🖼️ 결과 이미지")
    if st.session_state['final_img']:
        st.image(st.session_state['final_img'], caption="최종 결과물", use_container_width=True)
        
        # 다운로드
        buf = io.BytesIO()
        st.session_state['final_img'].save(buf, format="PNG")
        st.download_button("💾 이미지 다운로드", buf.getvalue(), "shorts_rank.png", "image/png", use_container_width=True)
    else:
        st.info("왼쪽에서 내용을 확정한 후 [Step 2] 버튼을 눌러주세요.")