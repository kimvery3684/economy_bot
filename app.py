import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import requests # 👈 구글 라이브러리 삭제! 기본 인터넷 접속 도구 사용
import json

# ==========================================
# 👇 [필수] API 키를 따옴표("") 사이에 공백 없이 붙여넣으세요.
GEMINI_API_KEY = "AIzaSyC-QRPifVhQGIGCjxk2kKDC0htuyiG0fTk"
# ==========================================

# --- 1. 🧠 제미나이 수동 접속 함수 (REST API) ---
def generate_pure_content(topic):
    # 키 입력 검사
    if len(GEMINI_API_KEY) < 10 or "여기에" in GEMINI_API_KEY:
        st.error("🚨 API 키 오류: 코드 상단의 GEMINI_API_KEY를 수정해주세요.")
        return None

    # 1. 구글 서버 주소 (라이브러리 없이 직접 연결)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 2. 보낼 편지 (헤더와 내용)
    headers = {'Content-Type': 'application/json'}
    
    # 3. 팩트 체크 프롬프트
    prompt_text = f"""
    너는 데이터에 집착하는 '팩트 폭격기' 유튜브 쇼츠 작가야.
    주제: '{topic}'
    
    위 주제로 TOP 10 랭킹을 작성하되, 아래 **[엄격한 검증 규칙]**을 헌법처럼 지켜라.
    
    [🚫 검증 및 선정 기준 (절대 준수)]
    1. **객관적 사실(Fact) 원칙**: 구글/위키피디아/국제 언론/공식 통계 자료 등에서 교차 검증된 정보만 사용해.
    2. **출처 제한**: 출처가 불분명하거나, 주장에 가까운 정보, 개인 블로그/커뮤니티 썰은 절대 제외해.
    3. **명확한 정의**: 기준이 명확한 수치, 연도, 기록, 공식 명칭으로 딱 떨어지는 항목만 선정해.
    
    [✍️ 작성 포맷]
    아래 형식을 토씨 하나 틀리지 말고 지켜. (인사말/사족 금지)
    
    1. 순위 및 명칭 - 핵심설명 (20자 이내)
       (객관적 근거: 정확한 수치 또는 공식 기록 요약 1줄)
    
    2. 순위 및 명칭 - 핵심설명 (20자 이내)
       (객관적 근거: 정확한 수치 또는 공식 기록 요약 1줄)
    
    ... (10위까지 작성)
    """
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }]
    }

    try:
        # 4. 전송 (POST 요청)
        response = requests.post(url, headers=headers, json=payload)
        
        # 5. 응답 확인 (성공 시 200 OK)
        if response.status_code == 200:
            result = response.json()
            # 텍스트 추출
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            # 🔥 [블랙박스] 실패 시 구글이 보낸 에러 메시지를 그대로 화면에 출력
            st.error(f"❌ 구글 서버 거절 (코드 {response.status_code})")
            st.code(response.text, language="json") # 에러 내용을 상세히 보여줌
            return None

    except Exception as e:
        st.error(f"❌ 인터넷 연결 오류: {e}")
        return None

# --- 2. 🎨 이미지 생성 함수 ---
def create_ranking_image(topic, text_content):
    W, H = 1080, 1350 
    img = Image.new('RGB', (W, H), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 70) 
        font_list = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 40)
        font_sub = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 30)
        font_desc = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 25)
    except:
        font_title = ImageFont.load_default()
        font_list = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_desc = ImageFont.load_default()

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

    draw.text((50, 270), "FACT CHECK RANKING", font=font_sub, fill="gray")

    # 리스트 그리기
    lines = text_content.strip().split('\n')
    start_y = 350
    
    count = 0
    for line in lines:
        clean_line = line.strip()
        if not clean_line: continue
        
        # 랭킹 항목
        if clean_line[0].isdigit() and "." in clean_line[:4]:
            count += 1
            if count > 10: break
            
            if len(clean_line) > 28: clean_line = clean_line[:28] + "..."
            color = (255, 215, 0) if count <= 3 else "white"
            draw.text((80, start_y), clean_line, font=font_list, fill=color)
            start_y += 60

        # 근거 항목
        elif clean_line.startswith("(") or "근거" in clean_line:
            draw.text((100, start_y), clean_line, font=font_desc, fill=(200, 200, 200))
            start_y += 50

    footer = "구독 🙏 좋아요 ❤️"
    bbox_foot = draw.textbbox((0, 0), footer, font=font_list)
    draw.text(((W - (bbox_foot[2] - bbox_foot[0]))/2, H - 100), footer, font=font_list, fill=(255, 100, 100))

    return img

# --- 3. 메인 화면 ---
st.set_page_config(page_title="팩트체크 쇼츠 공장", page_icon="⚖️", layout="wide")
st.title("⚖️ 3호점: 팩트체크 쇼츠 공장 (Direct)")

if 'draft' not in st.session_state:
    st.session_state['draft'] = ""
if 'img' not in st.session_state:
    st.session_state['img'] = None

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 주제 입력 (검증된 데이터)")
    topic = st.text_input("주제", value="세계에서 가장 비싼 기업 TOP 10")
    
    if st.button("🔍 팩트 기반 분석 + 이미지 생성", use_container_width=True, type="primary"):
        with st.spinner("구글 서버에 직접 접속 중입니다..."):
            ai_result = generate_pure_content(topic)
            
            if ai_result:
                st.session_state['draft'] = ai_result
                st.session_state['img'] = create_ranking_image(topic, ai_result)
                st.success("검증 완료!")

    # 수정 공간
    edited_text = st.text_area(
        "내용 수정 (근거 데이터 포함)", 
        value=st.session_state['draft'],
        height=400
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
        st.download_button("💾 이미지 다운로드", buf.getvalue(), "fact_ranking.png", "image/png", use_container_width=True)