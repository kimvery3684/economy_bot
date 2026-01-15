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
# 👇 API 키 입력 (따옴표 필수!)
GEMINI_API_KEY = "AIzaSyC-QRPifVhQGIGCjxk2kKDC0htuyiG0fTk"
# ==========================================

# --- 1. 네이버 검색 함수 ---
def naver_blog_search(keyword):
    client_id = "sk0nUwhPD16DNEo0gQkD"
    client_secret = "1cLzXGU3Yn"
    
    clean_keyword = keyword.replace('"', '').replace("'", "")
    encText = urllib.parse.quote(clean_keyword)
    # 검색 개수를 30개로 늘려 더 많은 정보를 줍니다
    url = f"https://openapi.naver.com/v1/search/blog?query={encText}&display=30&sort=sim" 
    
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

# --- 2. 🤖 제미나이 연결 (모델 자동 감지 시스템) ---
def get_gemini_response(topic, raw_data):
    if len(GEMINI_API_KEY) < 10 or "여기에" in GEMINI_API_KEY:
        st.error("API 키를 입력해주세요!")
        return None

    # 데이터 정리
    context = ""
    for item in raw_data:
        t = item['title'].replace('<b>', '').replace('</b>', '')
        d = item['description'].replace('<b>', '').replace('</b>', '')
        context += f"블로그글: {t} / 내용: {d}\n"

    # 프롬프트 (중요: 블로그 제목 나열하지 말고, 내용을 분석해서 하나로 합치라고 명령)
    prompt = f"""
    너는 베테랑 경제 분석가야. 아래 수집된 블로그 글들을 다 읽고 분석해서 '{topic}'에 해당하는 가장 강력한 TOP 10 항목을 뽑아내.
    
    [절대 규칙]
    1. 블로그 제목을 그대로 베끼지 마. 내용을 종합해서 구체적인 '종목명'이나 '아이템명'을 추출해.
    2. 중복된 내용은 하나로 합쳐.
    3. 결과는 오직 아래 포맷으로만 출력해 (사족, 인사말 금지):
       1. 아이템명 - 핵심특징(15자 이내)
       2. 아이템명 - 핵심특징(15자 이내)
       ...
    
    [수집된 데이터]
    {context}
    """

    genai.configure(api_key=GEMINI_API_KEY)

    # 🔥 [핵심] 3단계 모델 돌려막기 (하나라도 걸려라)
    models_to_try = ['gemini-1.5-flash', 'gemini-pro', 'gemini-1.0-pro']
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text.strip() # 성공하면 바로 반환
        except Exception:
            continue # 실패하면 다음 모델 시도

    # 3개 다 실패했을 경우
    st.error("모든 AI 모델 연결에 실패했습니다. API 키가 정확한지 확인해주세요.")
    return None

# --- 3. 이미지 생성 함수 ---
def create_ranking_image(topic, text_content):
    W, H = 1080, 1350 
    img = Image.new('RGB', (W, H), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 70) 
        font_list = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 42)
        font_sub = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 30)
    except:
        font_title = ImageFont.load_default()
        font_list = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # 디자인
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

    draw.text((50, 270), "TOP 10 RANKING", font=font_sub, fill="gray")

    # 리스트 그리기
    lines = text_content.strip().split('\n')
    start_y = 350
    gap = 90
    
    count = 0
    for line in lines:
        clean_line = line.strip()
        # 숫자나 점(.) 제거하고 깔끔하게 정리
        if not clean_line: continue
        
        # AI가 "1. 삼성전자" 식으로 줄 텐데, 이미지엔 깔끔하게 넣기 위해
        count += 1
        if count > 10: break
        
        if len(clean_line) > 26: clean_line = clean_line[:26] + "..."
        
        # 1~3위 강조 색상
        color = (255, 215, 0) if count <= 3 else "white"
        draw.text((80, start_y), clean_line, font=font_list, fill=color)
        start_y += gap

    footer = "구독 🙏 좋아요 ❤️"
    bbox_foot = draw.textbbox((0, 0), footer, font=font_list)
    draw.text(((W - (bbox_foot[2] - bbox_foot[0]))/2, H - 100), footer, font=font_list, fill=(255, 100, 100))

    return img

# --- 4. 메인 화면 ---
st.set_page_config(page_title="완전 자동 쇼츠 공장", page_icon="🏭", layout="wide")
st.title("🏭 3호점: AI 완전 자동화 공장")

if 'draft' not in st.session_state:
    st.session_state['draft'] = ""
if 'img' not in st.session_state:
    st.session_state['img'] = None

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 주제 입력")
    topic = st.text_input("주제", value="2025년 뜨는 창업 아이템 TOP 10")
    
    # 통합 버튼
    if st.button("🚀 검색 + 요약 + 이미지 생성 (원클릭)", use_container_width=True, type="primary"):
        with st.spinner("AI가 블로그 30개를 읽고 순위를 매기는 중입니다..."):
            # 1. 검색
            raw_data = naver_blog_search(topic)
            if raw_data:
                # 2. AI 요약 (모델 3개 돌려막기)
                ai_result = get_gemini_response(topic, raw_data)
                
                if ai_result:
                    st.session_state['draft'] = ai_result
                    # 3. 이미지 바로 생성
                    st.session_state['img'] = create_ranking_image(topic, ai_result)
                    st.success("생성 완료! 내용을 확인하세요.")
                else:
                    st.error("AI 연결에 실패했습니다. 잠시 후 다시 시도해주세요.")
            else:
                st.error("검색 결과가 없습니다.")

    # 수정 공간
    edited_text = st.text_area(
        "내용 확인 및 수정 (이미지에 들어갈 내용)", 
        value=st.session_state['draft'],
        height=350
    )
    
    # 수정 반영 버튼
    if st.button("🔄 수정한 내용으로 이미지 다시 만들기"):
        if edited_text:
            st.session_state['img'] = create_ranking_image(topic, edited_text)
            st.success("수정 완료!")

with col2:
    st.subheader("🖼️ 결과물")
    if st.session_state['img']:
        st.image(st.session_state['img'], caption="최종 결과", use_container_width=True)
        
        buf = io.BytesIO()
        st.session_state['img'].save(buf, format="PNG")
        st.download_button("💾 이미지 다운로드", buf.getvalue(), "ranking_final.png", "image/png", use_container_width=True)
    else:
        st.info("왼쪽 버튼을 누르면 AI가 분석한 결과가 나옵니다.")