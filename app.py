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
# 👇 [필수] 제미나이 API 키를 여기에 붙여넣으세요! (따옴표 필수)
GEMINI_API_KEY = "AIzaSyC-QRPifVhQGIGCjxk2kKDC0htuyiG0fTk"
# ==========================================

# --- 1. 📰 네이버 '뉴스' 검색 (블로그 X, 전문기사 O) ---
def naver_news_search(keyword):
    # 사장님이 처음에 주신 네이버 키를 적용했습니다 (확실한 작동 보장)
    client_id = "sk0nUwhPD16DNEo0gQkD"
    client_secret = "1cLzXGU3Yn"
    
    clean_keyword = keyword.replace('"', '').replace("'", "")
    encText = urllib.parse.quote(clean_keyword)
    
    # 'news' 카테고리로 변경하여 신뢰도 급상승
    # display=30: 기사 30개를 읽어서 정밀 분석
    url = f"https://openapi.naver.com/v1/search/news.json?query={encText}&display=30&sort=sim" 
    
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    
    try:
        response = urllib.request.urlopen(request)
        if response.getcode() == 200:
            return json.loads(response.read().decode('utf-8'))['items']
    except Exception as e:
        st.error(f"네이버 검색 오류: {e}")
        return None
    return None

# --- 2. 🤖 제미나이 분석 (뉴스 기사 기반) ---
def get_gemini_analysis(topic, news_data):
    if len(GEMINI_API_KEY) < 10 or "여기에" in GEMINI_API_KEY:
        st.error("🚨 API 키가 없습니다. 코드 상단에 키를 입력해주세요.")
        return None

    # 뉴스 데이터 텍스트화
    context = ""
    for item in news_data:
        # 뉴스 제목과 요약본 추출 (HTML 태그 제거)
        title = re.sub('<.*?>', '', item['title']).replace('&quot;', '"')
        desc = re.sub('<.*?>', '', item['description']).replace('&quot;', '"')
        context += f"기사: {title} / 내용: {desc}\n"

    # 제미나이에게 내리는 '전문가' 명령
    prompt = f"""
    너는 30년 경력의 경제 전문 기자야. 
    아래 '최신 뉴스 기사들'을 종합 분석해서 '{topic}'에 대한 TOP 10 랭킹을 작성해.
    
    [분석 원칙]
    1. 블로그의 '카더라' 정보가 아닌, 뉴스 기사의 '팩트'를 기반으로 해.
    2. 중복된 이슈는 하나로 합치고, 가장 중요한 키워드를 뽑아내.
    3. 설명은 독자가 혹할 수 있도록 핵심만 20자 이내로 요약해.
    
    [출력 양식] (이 양식 그대로만 출력할 것)
    1. 핵심키워드 - 핵심설명
    2. 핵심키워드 - 핵심설명
    ...
    
    [뉴스 데이터]
    {context}
    """

    genai.configure(api_key=GEMINI_API_KEY)

    # 모델 자동 연결 시도 (안정성 확보)
    models = ['gemini-1.5-flash', 'gemini-pro', 'gemini-1.0-pro']
    
    for model_name in models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text.strip()
        except:
            continue

    st.error("AI 연결이 지연되고 있습니다. 잠시 후 다시 시도해주세요.")
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

    # 디자인 요소
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

    draw.text((50, 270), "NEWS DATA ANALYSIS", font=font_sub, fill="gray")

    # 리스트 그리기
    lines = text_content.strip().split('\n')
    start_y = 350
    gap = 90
    
    count = 0
    for line in lines:
        clean_line = line.strip()
        if not clean_line: continue
        
        # 숫자로 시작하는 라인만 추출
        if len(clean_line) > 0 and clean_line[0].isdigit():
            count += 1
            if count > 10: break
            
            if len(clean_line) > 26: clean_line = clean_line[:26] + "..."
            
            color = (255, 215, 0) if count <= 3 else "white"
            draw.text((80, start_y), clean_line, font=font_list, fill=color)
            start_y += gap

    footer = "구독 🙏 좋아요 ❤️"
    bbox_foot = draw.textbbox((0, 0), footer, font=font_list)
    draw.text(((W - (bbox_foot[2] - bbox_foot[0]))/2, H - 100), footer, font=font_list, fill=(255, 100, 100))

    return img

# --- 4. 메인 화면 ---
st.set_page_config(page_title="뉴스 기반 쇼츠 공장", page_icon="📰", layout="wide")
st.title("📰 3호점: 뉴스 데이터 쇼츠 공장")

if 'draft' not in st.session_state:
    st.session_state['draft'] = ""
if 'img' not in st.session_state:
    st.session_state['img'] = None

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 주제 입력 (뉴스 데이터 기반)")
    topic = st.text_input("주제", value="2025년 급부상하는 AI 기업 TOP 10")
    
    if st.button("🚀 뉴스 검색 + AI 분석 + 이미지 생성", use_container_width=True, type="primary"):
        with st.spinner("최신 뉴스 기사 30개를 분석 중입니다..."):
            # 1. 네이버 뉴스 검색 (확실한 데이터)
            news_data = naver_news_search(topic)
            
            if news_data:
                # 2. 제미나이 분석
                ai_result = get_gemini_analysis(topic, news_data)
                
                if ai_result:
                    st.session_state['draft'] = ai_result
                    # 3. 이미지 생성
                    st.session_state['img'] = create_ranking_image(topic, ai_result)
                    st.success("뉴스 분석 완료! 결과를 확인하세요.")
                else:
                    st.error("AI 연결에 실패했습니다. (키를 확인하세요)")
            else:
                st.error("관련 뉴스 기사가 없습니다.")

    # 수정 공간
    edited_text = st.text_area(
        "내용 수정 (뉴스 분석 결과)", 
        value=st.session_state['draft'],
        height=350
    )
    
    if st.button("🔄 수정사항 반영해서 이미지 다시 만들기"):
        if edited_text:
            st.session_state['img'] = create_ranking_image(topic, edited_text)
            st.success("반영 완료!")

with col2:
    st.subheader("🖼️ 결과물")
    if st.session_state['img']:
        st.image(st.session_state['img'], caption="최종 결과", use_container_width=True)
        
        buf = io.BytesIO()
        st.session_state['img'].save(buf, format="PNG")
        st.download_button("💾 이미지 다운로드", buf.getvalue(), "news_ranking.png", "image/png", use_container_width=True)
    else:
        st.info("왼쪽 버튼을 누르면 뉴스를 분석해 순위표를 만듭니다.")