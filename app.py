import streamlit as st
import urllib.request
import urllib.parse
import json
import re
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import google.generativeai as genai

# ==========================================
# 👇 여기에 제미나이 API 키를 입력하세요! (따옴표 안에 넣기)
GEMINI_API_KEY = "AIzaSyC-QRPifVhQGIGCjxk2kKDC0htuyiG0fTk"
# ==========================================

# --- 1. 네이버 검색 함수 ---
def naver_blog_search(keyword):
    client_id = "sk0nUwhPD16DNEo0gQkD"
    client_secret = "1cLzXGU3Yn"
    
    clean_keyword = keyword.replace('"', '').replace("'", "")
    encText = urllib.parse.quote(clean_keyword)
    url = f"https://openapi.naver.com/v1/search/blog?query={encText}&display=20&sort=sim" 
    
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

# --- 2. 🤖 제미나이 지능형 요약 함수 ---
def ask_gemini_to_organize(topic, raw_data):
    """네이버 블로그 데이터를 제미나이에게 주고 깔끔한 랭킹으로 정리시킴"""
    if "여기에" in GEMINI_API_KEY:
        st.error("⚠️ 코드 맨 위 'GEMINI_API_KEY'에 키를 입력해주세요!")
        return []

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        
        # 블로그 데이터 텍스트화
        context = ""
        for item in raw_data:
            title = item['title'].replace('<b>', '').replace('</b>', '')
            desc = item['description'].replace('<b>', '').replace('</b>', '')
            context += f"- {title} : {desc}\n"

        # 제미나이 명령 (프롬프트)
        prompt = f"""
        너는 경제 유튜브 쇼츠 작가야. 아래 블로그 검색 결과를 분석해서 '{topic}'에 맞는 순위(TOP 10)를 만들어줘.
        
        [규칙]
        1. 광고는 빼고 진짜 정보만 골라.
        2. 출력은 오직 아래 형식으로만 해 (군더더기 말 절대 금지):
           1. 핵심키워드 - 간단한설명
           2. 핵심키워드 - 간단한설명
           ...
        
        [데이터]
        {context}
        """
        
        response = model.generate_content(prompt)
        lines = response.text.strip().split('\n')
        # 빈 줄 제거하고 리스트로 변환
        cleaned_list = [line for line in lines if line.strip() != ""]
        return cleaned_list[:10]

    except Exception as e:
        st.error(f"제미나이 오류: {e}")
        return []

# --- 3. 이미지 생성 함수 ---
def create_ranking_image(topic, ranking_list):
    W, H = 1080, 1350 
    img = Image.new('RGB', (W, H), color=(0, 0, 0)) # 검은 배경
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 70) 
        font_list = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 40)
        font_sub = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 35)
    except:
        font_title = ImageFont.load_default()
        font_list = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # 테두리 및 디자인
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

    draw.text((50, 270), "Analysis by Gemini AI", font=font_sub, fill="gray")

    # 리스트 그리기
    start_y = 350
    gap = 90
    for i, text in enumerate(ranking_list, 1):
        if len(text) > 28: text = text[:28] + "..."
        color = (255, 215, 0) if i <= 3 else "white"
        draw.text((80, start_y), text, font=font_list, fill=color)
        start_y += gap

    # 푸터
    footer = "구독 🙏 좋아요 ❤️"
    bbox_foot = draw.textbbox((0, 0), footer, font=font_list)
    draw.text(((W - (bbox_foot[2] - bbox_foot[0]))/2, H - 100), footer, font=font_list, fill=(255, 100, 100))

    return img

# --- 4. 메인 화면 ---
st.set_page_config(page_title="AI 경제 쇼츠 공장", page_icon="🤖", layout="wide")
st.title("🤖 3호점: 제미나이 탑재 쇼츠 공장")

if 'result_img' not in st.session_state:
    st.session_state['result_img'] = None

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 주제 입력")
    topic = st.text_input("주제", value="2025년 주목해야 할 AI 관련주 TOP 10")
    
    if st.button("✨ 제미나이! 검색+정리+이미지 원큐에 해줘", use_container_width=True, type="primary"):
        with st.spinner("1단계: 네이버 블로그 뒤지는 중... 🕵️"):
            raw_data = naver_blog_search(topic)
            
        if raw_data:
            with st.spinner("2단계: 제미나이가 순위 정리 중... 🧠"):
                clean_ranking = ask_gemini_to_organize(topic, raw_data)
                
                if clean_ranking:
                    with st.spinner("3단계: 이미지 생성 중... 🎨"):
                        img = create_ranking_image(topic, clean_ranking)
                        st.session_state['result_img'] = img
                        st.success("완료!")
                else:
                    st.error("제미나이 키를 확인해주세요!")
        else:
            st.error("검색 결과가 없습니다.")

with col2:
    st.subheader("🖼️ 결과물")
    if st.session_state['result_img']:
        st.image(st.session_state['result_img'], caption="Gemini 결과", use_container_width=True)
        
        buf = io.BytesIO()
        st.session_state['result_img'].save(buf, format="PNG")
        st.download_button("💾 이미지 저장", buf.getvalue(), "shorts_card.png", "image/png", use_container_width=True)
    else:
        st.info("왼쪽 버튼을 누르면 AI가 일을 시작합니다.")