import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import google.generativeai as genai

# ==========================================
# 👇 [필수] 제미나이 API 키를 여기에 붙여넣으세요! (따옴표 필수)
GEMINI_API_KEY = "AIzaSyC-QRPifVhQGIGCjxk2kKDC0htuyiG0fTk"
# ==========================================

# --- 1. 🧠 제미나이 순수 창작 함수 (검색 X, 지식 기반 O) ---
def generate_pure_content(topic):
    # 키 입력 확인
    if len(GEMINI_API_KEY) < 10 or "여기에" in GEMINI_API_KEY:
        st.error("🚨 API 키가 입력되지 않았습니다. 코드 상단을 확인해주세요.")
        return None

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # 전문가 페르소나 부여
        prompt = f"""
        너는 유튜브 쇼츠 콘텐츠를 전문으로 만드는 '천재 작가'야.
        주제: '{topic}'
        
        위 주제에 대해 사람들이 가장 흥미로워할 만한 **TOP 10 랭킹**을 너의 지식을 총동원해서 작성해.
        
        [작성 규칙]
        1. 뻔한 내용보다는 구체적이고 흥미로운 항목 위주로 구성해.
        2. 설명은 20자 이내로 짧고 강렬하게 (유튜브 시청자가 읽기 쉽게).
        3. 서론, 결론, 인사말 절대 금지. 오직 리스트만 출력해.
        
        [출력 포맷]
        1. 핵심키워드 - 핵심설명
        2. 핵심키워드 - 핵심설명
        ...
        (10위까지 작성)
        """

        # 모델 설정 (가장 똑똑한 모델부터 순차 시도)
        models = ['gemini-1.5-flash', 'gemini-pro', 'gemini-1.0-pro']
        
        for model_name in models:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return response.text.strip()
            except:
                continue # 실패하면 다음 모델로 넘어감

        st.error("AI 연결에 실패했습니다. (API 키 오류 또는 구글 서버 문제)")
        return None

    except Exception as e:
        st.error(f"오류 발생: {e}")
        return None

# --- 2. 🎨 이미지 생성 함수 (디자인 공장) ---
def create_ranking_image(topic, text_content):
    W, H = 1080, 1350 
    img = Image.new('RGB', (W, H), color=(0, 0, 0)) # 검은 배경
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 70) 
        font_list = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 42)
        font_sub = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 30)
    except:
        font_title = ImageFont.load_default()
        font_list = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # 빨간 테두리 디자인
    draw.rectangle([(0,0), (W, H)], outline=(255, 0, 0), width=15)
    draw.line([(0, 250), (W, 250)], fill=(255, 0, 0), width=5)

    # 제목 (자동 줄바꿈)
    para = textwrap.wrap(topic, width=16)
    current_h = 80
    for line in para:
        bbox = draw.textbbox((0, 0), line, font=font_title)
        text_w = bbox[2] - bbox[0]
        draw.text(((W - text_w) / 2, current_h), line, font=font_title, fill="white")
        current_h += 80

    draw.text((50, 270), "AI KNOWLEDGE RANKING", font=font_sub, fill="gray")

    # 리스트 그리기
    lines = text_content.strip().split('\n')
    start_y = 350
    gap = 90
    
    count = 0
    for line in lines:
        clean_line = line.strip()
        if not clean_line: continue
        
        # 숫자나 점 제거하고 내용만 추출 시도 (AI가 1. 2. 를 붙여줄 테니 그대로 사용)
        if len(clean_line) > 0 and clean_line[0].isdigit():
            count += 1
            if count > 10: break
            
            # 너무 길면 자르기
            if len(clean_line) > 26: clean_line = clean_line[:26] + "..."
            
            # 1~3위 금색 강조
            color = (255, 215, 0) if count <= 3 else "white"
            draw.text((80, start_y), clean_line, font=font_list, fill=color)
            start_y += gap

    footer = "구독 🙏 좋아요 ❤️"
    bbox_foot = draw.textbbox((0, 0), footer, font=font_list)
    draw.text(((W - (bbox_foot[2] - bbox_foot[0]))/2, H - 100), footer, font=font_list, fill=(255, 100, 100))

    return img

# --- 3. 메인 화면 ---
st.set_page_config(page_title="AI 지식 쇼츠 공장", page_icon="🧠", layout="wide")
st.title("🧠 3호점: 순수 AI 지식 공장")

if 'draft' not in st.session_state:
    st.session_state['draft'] = ""
if 'img' not in st.session_state:
    st.session_state['img'] = None

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 주제 입력 (AI 지식 기반)")
    topic = st.text_input("주제", value="2025년 최고의 다이어트 식단 TOP 10")
    
    # 통합 버튼
    if st.button("⚡ 제미나이 뇌 가동 + 이미지 생성", use_container_width=True, type="primary"):
        with st.spinner("제미나이가 알고리즘을 분석 중입니다..."):
            # 1. 제미나이에게 바로 물어보기 (검색 과정 생략)
            ai_result = generate_pure_content(topic)
            
            if ai_result:
                st.session_state['draft'] = ai_result
                # 2. 이미지 생성
                st.session_state['img'] = create_ranking_image(topic, ai_result)
                st.success("생성 완료!")
            else:
                # 에러 메시지는 함수 안에서 출력됨
                pass

    # 수정 공간
    edited_text = st.text_area(
        "내용 수정 (AI가 작성한 내용)", 
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
        st.download_button("💾 이미지 다운로드", buf.getvalue(), "ai_ranking.png", "image/png", use_container_width=True)
    else:
        st.info("왼쪽 버튼을 누르면 AI가 즉시 순위를 매깁니다.")