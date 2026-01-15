import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import requests
import json

# ==========================================
# 👇 [필수] API 키를 따옴표("") 안에 넣어주세요!
GEMINI_API_KEY = "AIzaSyC-QRPifVhQGIGCjxk2kKDC0htuyiG0fTk"
# ==========================================

# --- 1. 🕵️‍♂️ 사용 가능한 모델 자동 탐색 함수 ---
def get_valid_model_url():
    """구글 서버에 물어보고, 현재 사용 가능한 최적의 모델 주소를 찾아옵니다."""
    base_url = "https://generativelanguage.googleapis.com/v1beta/models"
    try:
        # 1. 모델 목록 조회 (GET 요청)
        response = requests.get(f"{base_url}?key={GEMINI_API_KEY}")
        
        if response.status_code == 200:
            models = response.json().get('models', [])
            # 2. '글쓰기(generateContent)' 기능이 있는 모델만 필터링
            valid_models = [
                m['name'] for m in models 
                if 'generateContent' in m.get('supportedGenerationMethods', [])
            ]
            
            if valid_models:
                # 3. 우리가 좋아하는 순서대로 우선순위 선택
                preferred_order = ['models/gemini-1.5-flash', 'models/gemini-pro', 'models/gemini-1.0-pro']
                
                # 선호 모델이 목록에 있으면 그거 선택
                for pref in preferred_order:
                    if pref in valid_models:
                        return f"https://generativelanguage.googleapis.com/v1beta/{pref}:generateContent"
                
                # 없으면 그냥 목록의 첫 번째 놈이라도 잡아옴 (무조건 작동 보장)
                return f"https://generativelanguage.googleapis.com/v1beta/{valid_models[0]}:generateContent"
        
        return None # 목록 조회 실패 시
    except:
        return None

# --- 2. ⚡ AI 콘텐츠 생성 (자동 탐색 주소 사용) ---
def generate_content_smart(topic):
    if len(GEMINI_API_KEY) < 10 or "여기에" in GEMINI_API_KEY:
        st.error("🚨 API 키가 입력되지 않았습니다.")
        return None

    # 1. 쓸 수 있는 모델 주소를 알아옴
    target_url = get_valid_model_url()
    
    # 2. 만약 모델을 못 찾으면 -> 가장 기본 주소로 강제 시도 (혹시 모르니까)
    if not target_url:
        target_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    
    # 3. 최종 접속 주소에다가 요청 발사!
    full_url = f"{target_url}?key={GEMINI_API_KEY}"
    
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
            # 4. 그래도 안 되면 에러 메시지 출력
            st.error(f"❌ 구글 연결 실패 ({response.status_code})")
            st.code(response.text, language="json")
            return None
            
    except Exception as e:
        st.error(f"❌ 연결 오류: {e}")
        return None

# --- 3. 🎨 이미지 생성 ---
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

# --- 4. 메인 화면 ---
st.set_page_config(page_title="스마트 AI 공장", page_icon="🧠", layout="wide")
st.title("🧠 3호점: 스스로 모델 찾는 똑똑한 공장")

if 'result_text' not in st.session_state:
    st.session_state['result_text'] = ""
if 'img' not in st.session_state:
    st.session_state['img'] = None

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 주제 입력")
    topic = st.text_input("주제", value="2025년 대박 날 아이템 TOP 10")
    
    if st.button("🚀 실행 (AI 자동 연결)", use_container_width=True, type="primary"):
        with st.spinner("사용 가능한 AI 모델을 탐색 중입니다..."):
            
            ai_result = generate_content_smart(topic)
            
            if ai_result:
                st.success("연결 성공! 이미지를 생성합니다.")
                st.session_state['result_text'] = ai_result
                st.session_state['img'] = create_ranking_image(topic, ai_result)
            else:
                pass # 에러 메시지 확인

    # 편집창
    edited_text = st.text_area(
        "내용 수정", 
        value=st.session_state['result_text'],
        height=350
    )
    
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