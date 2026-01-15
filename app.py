import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import google.generativeai as genai

# ==========================================
# 👇 [필수] 제미나이 API 키를 따옴표("") 안에 넣어주세요!
GEMINI_API_KEY = "AIzaSyC-QRPifVhQGIGCjxk2kKDC0htuyiG0fTk"
# ==========================================

# --- 1. 🧠 제미나이 직접 연결 (검색 없이 바로 작성) ---
def direct_ai_generation(topic):
    # 키 확인
    if len(GEMINI_API_KEY) < 10 or "여기에" in GEMINI_API_KEY:
        st.error("🚨 API 키가 없습니다. 코드 상단에 키를 입력해주세요.")
        return None

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash') # 속도 빠른 최신 모델
        
        # 프롬프트: 검색하지 말고 너의 지식으로 써라!
        prompt = f"""
        주제: '{topic}'
        
        위 주제에 대해 너의 방대한 지식을 동원해서 가장 인기 있고 흥미로운 **TOP 10 랭킹**을 작성해.
        
        [작성 규칙]
        1. 인터넷 검색하지 말고 네가 아는 정보를 바탕으로 써.
        2. 설명은 20자 이내로 짧고 강렬하게.
        3. 서론, 결론, 인사말 절대 금지. 오직 리스트만 출력해.
        
        [출력 포맷]
        1. 핵심키워드 - 핵심설명
        2. 핵심키워드 - 핵심설명
        ...
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        st.error(f"AI 연결 오류: {e}")
        return None

# --- 2. 🎨 이미지 생성 (디자인 공장) ---
def create_ranking_image(topic, text_content):
    W, H = 1080, 1350 
    img = Image.new('RGB', (W, H), color=(0, 0, 0)) # 검은 배경
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 70) 
        font_list = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 40)
        font_sub = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 30)
    except:
        font_title = ImageFont.load_default()
        font_list = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # 빨간 테두리
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

    draw.text((50, 270), "AI RANKING", font=font_sub, fill="gray")

    # 리스트 그리기
    lines = text_content.strip().split('\n')
    start_y = 350
    gap = 90
    
    count = 0
    for line in lines:
        clean_line = line.strip()
        if not clean_line: continue
        
        # 숫자로 시작하는 줄만 이미지에 넣기
        if clean_line[0].isdigit():
            count += 1
            if count > 10: break
            
            if len(clean_line) > 26: clean_line = clean_line[:26] + "..."
            
            # 1~3위 강조
            color = (255, 215, 0) if count <= 3 else "white"
            draw.text((80, start_y), clean_line, font=font_list, fill=color)
            start_y += gap

    footer = "구독 🙏 좋아요 ❤️"
    bbox_foot = draw.textbbox((0, 0), footer, font=font_list)
    draw.text(((W - (bbox_foot[2] - bbox_foot[0]))/2, H - 100), footer, font=font_list, fill=(255, 100, 100))

    return img

# --- 3. 메인 화면 ---
st.set_page_config(page_title="AI 직통 공장", page_icon="⚡", layout="wide")
st.title("⚡ 3호점: AI 직통 공장")

if 'result_text' not in st.session_state:
    st.session_state['result_text'] = ""
if 'img' not in st.session_state:
    st.session_state['img'] = None

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 주제 입력")
    topic = st.text_input("주제", value="2025년 대박 날 AI 관련주 TOP 10")
    
    # 버튼 하나로 해결
    if st.button("🚀 실행 (검색 없이 AI가 바로 작성)", use_container_width=True, type="primary"):
        with st.spinner("제미나이가 머리를 굴리는 중입니다..."):
            # 검색 과정 삭제! 바로 AI 호출
            ai_result = direct_ai_generation(topic)
            
            if ai_result:
                st.session_state['result_text'] = ai_result
                # 바로 이미지 생성
                st.session_state['img'] = create_ranking_image(topic, ai_result)
                st.success("작성 완료!")
            else:
                pass # 에러는 함수 안에서 처리

    # 결과 수정란
    edited_text = st.text_area(
        "AI가 쓴 내용 수정하기", 
        value=st.session_state['result_text'],
        height=350
    )
    
    if st.button("🔄 수정한 내용으로 이미지 다시 만들기"):
        if edited_text:
            st.session_state['img'] = create_ranking_image(topic, edited_text)
            st.success("반영 완료!")

with col2:
    st.subheader("🖼️ 결과물")
    if st.session_state['img']:
        st.image(st.session_state['img'], caption="최종 결과", use_container_width=True)
        
        buf = io.BytesIO()
        st.session_state['img'].save(buf, format="PNG")
        st.download_button("💾 이미지 다운로드", buf.getvalue(), "ai_result.png", "image/png", use_container_width=True)
    else:
        st.info("왼쪽 버튼을 누르면 AI가 즉시 내용을 채웁니다.")