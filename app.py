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

# --- 1. 🧠 제미나이 진단 연결 (에러 숨기기 없음) ---
def debug_ai_connection(topic):
    # 키 확인
    if len(GEMINI_API_KEY) < 10 or "여기에" in GEMINI_API_KEY:
        st.error("🚨 [치명적 오류] API 키가 입력되지 않았습니다!")
        st.write("👉 코드의 `GEMINI_API_KEY = ...` 부분을 확인해주세요.")
        return None

    # 주소 (가장 안정적인 1.5-flash 모델)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    prompt = f"주제 '{topic}'에 대한 TOP 10 랭킹을 작성해줘."
    
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        # 전송
        response = requests.post(url, headers=headers, json=data)
        
        # ✅ 성공 (200 OK)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        
        # ❌ 실패 (구글이 거절함) -> 원인 출력!
        else:
            st.error(f"❌ 구글 서버 연결 거부 (에러코드: {response.status_code})")
            st.warning("👇 구글이 보낸 에러 메시지 원본:")
            st.code(response.text, language="json") # 에러 내용을 적나라하게 보여줌
            return None

    except Exception as e:
        st.error(f"❌ 인터넷/파이썬 내부 오류: {e}")
        return None

# --- 2. 🎨 이미지 생성 ---
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
        count += 1
        if count > 10: break
        if len(clean) > 28: clean = clean[:28] + "..."
        draw.text((80, start_y), clean, font=font_list, fill="white")
        start_y += gap

    return img

# --- 3. 메인 화면 ---
st.set_page_config(page_title="AI 정밀 진단", page_icon="🩺", layout="wide")
st.title("🩺 3호점: AI 연결 정밀 진단 모드")

if 'result_text' not in st.session_state:
    st.session_state['result_text'] = ""
if 'img' not in st.session_state:
    st.session_state['img'] = None

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 주제 입력")
    topic = st.text_input("주제", value="테스트")
    
    if st.button("🚀 원인 분석 실행 (에러를 보여줘!)", use_container_width=True, type="primary"):
        with st.spinner("구글 서버에 노크하는 중..."):
            ai_result = debug_ai_connection(topic)
            
            if ai_result:
                st.success("✅ 성공! (API 키가 정상입니다)")
                st.session_state['result_text'] = ai_result
                st.session_state['img'] = create_ranking_image(topic, ai_result)
            else:
                st.error("🚫 실패! 위 에러 메시지를 확인하세요.")

with col2:
    st.subheader("🖼️ 결과물")
    if st.session_state['img']:
        st.image(st.session_state['img'], caption="결과", use_container_width=True)