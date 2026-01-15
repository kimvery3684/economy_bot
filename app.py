import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import requests
import json

# --- 메인 화면 설정 ---
st.set_page_config(page_title="보안 강화 AI 공장", page_icon="🔐", layout="wide")
st.title("🔐 3호점: 보안이 강화된 AI 쇼츠 공장")

# --- 1. 사이드바: API 키 입력 (안전 구역) ---
with st.sidebar:
    st.header("🔑 열쇠 보관소")
    st.info("API 키를 코드에 적지 마세요! 해킹 당합니다.")
    # 여기에 입력하면 안전하게 처리됩니다.
    user_api_key = st.text_input("새로 받은 API 키를 입력하세요", type="password")
    
    if user_api_key:
        st.success("키가 입력되었습니다! 작동 준비 완료.")
    else:
        st.warning("👈 먼저 이곳에 키를 넣어주세요.")

# --- 2. 🕵️‍♂️ 모델 자동 탐색 ---
def get_valid_model_url(api_key):
    """입력된 키로 사용 가능한 모델을 찾아냅니다."""
    base_url = "https://generativelanguage.googleapis.com/v1beta/models"
    try:
        response = requests.get(f"{base_url}?key={api_key}")
        if response.status_code == 200:
            models = response.json().get('models', [])
            valid_models = [m['name'] for m in models if 'generateContent' in m.get('supportedGenerationMethods', [])]
            
            # 우선순위: 1.5-flash -> pro
            preferred = ['models/gemini-1.5-flash', 'models/gemini-pro']
            for p in preferred:
                if p in valid_models:
                    return f"https://generativelanguage.googleapis.com/v1beta/{p}:generateContent"
            return f"https://generativelanguage.googleapis.com/v1beta/{valid_models[0]}:generateContent"
        return None
    except:
        return None

# --- 3. ⚡ AI 콘텐츠 생성 ---
def generate_content_safe(topic, api_key):
    # 키가 없으면 실행 안 함
    if not api_key:
        st.error("좌측 사이드바에 API 키를 먼저 입력해주세요!")
        return None

    # 모델 주소 찾기
    target_url = get_valid_model_url(api_key)
    if not target_url:
        target_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    
    full_url = f"{target_url}?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    prompt = f"""
    주제: '{topic}'
    위 주제에 대해 가장 인기 있는 TOP 10 랭킹을 작성해.
    
    [작성 규칙]
    1. 인터넷 검색하지 말고 네가 아는 정보를 바탕으로 써.
    2. 설명은 20자 이내로 짧고 강렬하게.
    3. 서론, 결론, 인사말 절대 금지. 오직 리스트만 출력해.
    
    [출력 포맷]
    1. 항목명 - 핵심설명
    2. 항목명 - 핵심설명
    ...
    """
    
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(full_url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            st.error(f"❌ 구글 연결 실패 ({response.status_code})")
            st.code(response.text)
            return None
    except Exception as e:
        st.error(f"❌ 연결 오류: {e}")
        return None

# --- 4. 🎨 이미지 생성 ---
def create_ranking_image(topic, text_content):
    W, H = 1080, 1350 
    img = Image.new('RGB', (W, H), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 70) 
        font_list = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 40)
    except:
        font_title = ImageFont.load_default()
        font_list = ImageFont.load_default()

    draw.rectangle([(0,0), (W, H)], outline=(255, 0, 0), width=15)
    draw.line([(0, 250), (W, 250)], fill=(255, 0, 0), width=5)

    para = textwrap.wrap(topic, width=16)
    current_h = 80
    for line in para:
        bbox = draw.textbbox((0, 0), line, font=font_title)
        text_w = bbox[2] - bbox[0]
        draw.text(((W - text_w) / 2, current_h), line, font=font_title, fill="white")
        current_h += 80

    lines = text_content.strip().split('\n')
    start_y = 350
    gap = 90
    
    count = 0
    for line in lines:
        clean = line.strip()
        if not clean: continue
        if clean[0].isdigit():
            count += 1
            if count > 10: break
            if len(clean) > 28: clean = clean[:28] + "..."
            color = (255, 215, 0) if count <= 3 else "white"
            draw.text((80, start_y), clean, font=font_list, fill=color)
            start_y += gap

    return img

# --- 5. 메인 레이아웃 ---
if 'result_text' not in st.session_state:
    st.session_state['result_text'] = ""
if 'img' not in st.session_state:
    st.session_state['img'] = None

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 주제 입력")
    topic = st.text_input("주제", value="2025년 대박 날 아이템 TOP 10")
    
    if st.button("🚀 실행 (보안 모드)", use_container_width=True, type="primary"):
        # 키가 입력되었는지 확인 후 실행
        if user_api_key:
            with st.spinner("안전하게 AI에 접속 중입니다..."):
                ai_result = generate_content_safe(topic, user_api_key)
                if ai_result:
                    st.success("성공!")
                    st.session_state['result_text'] = ai_result
                    st.session_state['img'] = create_ranking_image(topic, ai_result)
        else:
            st.error("👈 왼쪽 사이드바에 API 키를 먼저 넣어주세요!")

    edited_text = st.text_area("내용 수정", value=st.session_state['result_text'], height=350)
    
    if st.button("🔄 수정사항 반영"):
        if edited_text:
            st.session_state['img'] = create_ranking_image(topic, edited_text)
            st.success("완료!")

with col2:
    st.subheader("🖼️ 결과물")
    if st.session_state['img']:
        st.image(st.session_state['img'], caption="결과", use_container_width=True)
        buf = io.BytesIO()
        st.session_state['img'].save(buf, format="PNG")
        st.download_button("💾 다운로드", buf.getvalue(), "result.png", "image/png", use_container_width=True)