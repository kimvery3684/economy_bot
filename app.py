import streamlit as st
import urllib.request
import urllib.parse
import json
import re
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import google.generativeai as genai  # 라이브러리 사용 (REST 방식 폐기)

# ==========================================
# 👇 API 키 입력 (따옴표 필수!)
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
    except:
        return None
    return None

# --- 2. ⚡ 비상용: 파이썬 단순 정리 함수 (AI 고장 시 작동) ---
def fallback_formatter(raw_data):
    """AI가 안 될 때, 코드가 직접 제목과 내용을 잘라서 정리함"""
    result_text = ""
    for i, item in enumerate(raw_data[:10], 1):
        # HTML 태그 제거
        title = item['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
        desc = item['description'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
        
        # 너무 긴 내용은 자름
        if len(desc) > 30: desc = desc[:30] + "..."
        
        result_text += f"{i}. {title}\n   - 설명: {desc}\n"
    return result_text

# --- 3. 🤖 제미나이 연결 (실패 시 비상용 함수 호출) ---
def get_draft_content(topic, raw_data):
    # 1. 키가 없으면 바로 비상 모드
    if len(GEMINI_API_KEY) < 10 or "여기에" in GEMINI_API_KEY:
        st.toast("⚠️ API 키 없음: 비상 모드로 정리합니다.")
        return fallback_formatter(raw_data)

    # 2. 제미나이 시도
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash") # 최신 모델
        
        context = ""
        for item in raw_data:
            t = item['title'].replace('<b>', '').replace('</b>', '')
            d = item['description'].replace('<b>', '').replace('</b>', '')
            context += f"- {t} : {d}\n"

        prompt = f"""
        주제: '{topic}'
        위 데이터를 바탕으로 유튜브 쇼츠용 랭킹 TOP 10을 작성해.
        
        [조건]
        1. 인사말, 서론 절대 금지. 오직 리스트만 출력.
        2. 형식: "순위. 키워드 - 짧은설명"
        3. 설명은 20자 이내로 핵심만.
        
        [데이터]
        {context}
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        # 🔥 여기가 핵심! AI 에러 나면 당황하지 않고 비상 함수 가동
        st.toast(f"🤖 AI 연결 불안정 ({e}). 비상 시스템 가동!")
        return fallback_formatter(raw_data)

# --- 4. 이미지 생성 함수 ---
def create_ranking_image(topic, text_content):
    W, H = 1080, 1350 
    img = Image.new('RGB', (W, H), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 70) 
        font_list = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 40)
        font_sub = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 30)
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

    draw.text((50, 270), "Ranking System", font=font_sub, fill="gray")

    # 내용 그리기
    lines = text_content.strip().split('\n')
    start_y = 350
    gap = 90
    
    count = 0
    for line in lines:
        clean_line = line.strip()
        if not clean_line: continue
        
        # '1. ' 처럼 숫자로 시작하는 줄만 이미지에 넣기
        if line[0].isdigit():
            count += 1
            if count > 10: break
            
            # 너무 길면 자르기
            if len(clean_line) > 28: clean_line = clean_line[:28] + "..."
            
            color = (255, 215, 0) if count <= 3 else "white"
            draw.text((80, start_y), clean_line, font=font_list, fill=color)
            start_y += gap

    footer = "구독 🙏 좋아요 ❤️"
    bbox_foot = draw.textbbox((0, 0), footer, font=font_list)
    draw.text(((W - (bbox_foot[2] - bbox_foot[0]))/2, H - 100), footer, font=font_list, fill=(255, 100, 100))

    return img

# --- 5. 메인 화면 ---
st.set_page_config(page_title="무중단 쇼츠 공장", page_icon="🏭", layout="wide")
st.title("🏭 3호점: 절대 멈추지 않는 공장")

if 'draft' not in st.session_state:
    st.session_state['draft'] = ""
if 'img' not in st.session_state:
    st.session_state['img'] = None

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 콘텐츠 편집")
    topic = st.text_input("주제", value="2025년 뜨는 창업 아이템 TOP 10")
    
    if st.button("Step 1. 데이터 수집 및 초안 작성 📝", use_container_width=True):
        with st.spinner("데이터를 긁어오는 중..."):
            raw_data = naver_blog_search(topic)
            if raw_data:
                # 여기서 AI가 안 되면 -> 자동으로 '비상용 함수'가 작동함
                st.session_state['draft'] = get_draft_content(topic, raw_data)
                st.success("작성 완료! 아래 내용을 입맛대로 수정하세요.")
            else:
                st.error("네이버 검색 결과가 없습니다.")

    # 편집기
    text_input = st.text_area(
        "내용 수정 (AI가 쓴 게 맘에 안 들면 직접 고치세요!)", 
        value=st.session_state['draft'],
        height=400
    )

    if st.button("Step 2. 결과물 이미지 생성 🎨", use_container_width=True, type="primary"):
        if text_input:
            st.session_state['img'] = create_ranking_image(topic, text_input)
        else:
            st.warning("내용이 없습니다.")

with col2:
    st.subheader("🖼️ 완성된 이미지")
    if st.session_state['img']:
        st.image(st.session_state['img'], caption="최종 결과", use_container_width=True)
        
        buf = io.BytesIO()
        st.session_state['img'].save(buf, format="PNG")
        st.download_button("💾 다운로드", buf.getvalue(), "ranking.png", "image/png", use_container_width=True)