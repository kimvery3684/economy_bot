import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import requests
import json
import random

# ==========================================
# 👇 [필수] API 키를 따옴표("") 안에 넣어주세요!
GEMINI_API_KEY = "AIzaSyC-QRPifVhQGIGCjxk2kKDC0htuyiG0fTk"
# ==========================================

# --- 1. 🚨 비상용 원고 생성기 (AI 고장 시 작동) ---
def emergency_backup_generator(topic):
    """AI 연결 실패 시, 코드가 직접 그럴듯한 초안을 만듭니다."""
    st.toast("⚠️ AI 연결 불안정 -> '비상 모드'로 초안을 생성했습니다.")
    
    # 그럴듯한 랭킹 템플릿
    templates = [
        f"가장 주목해야 할 {topic} 트렌드",
        f"{topic}의 혁신적인 변화",
        f"수익률을 극대화하는 {topic} 전략",
        f"2025년 {topic} 핵심 키워드",
        f"절대 놓쳐선 안 될 {topic} 정보",
        f"전문가가 추천하는 {topic} BEST",
        f"{topic} 성공을 위한 필수 조건",
        f"지금 당장 시작해야 할 {topic}",
        f"{topic} 시장의 새로운 기회",
        f"실패 없는 {topic} 노하우"
    ]
    
    # 텍스트 생성
    result_text = ""
    for i, item in enumerate(templates, 1):
        result_text += f"{i}. {item} - 상세 내용은 직접 수정해주세요.\n"
    
    return result_text

# --- 2. 🧠 제미나이 다중 접속 시도 (Multi-Try) ---
def direct_ai_generation(topic):
    if len(GEMINI_API_KEY) < 10 or "여기에" in GEMINI_API_KEY:
        st.error("🚨 API 키가 없습니다. 키를 입력하거나 비상 모드로 진행합니다.")
        return emergency_backup_generator(topic)

    # 시도할 모델 주소 리스트 (순서대로 전화 걸어봄)
    urls = [
        # 1순위: 최신 1.5 Flash (빠름)
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
        # 2순위: 1.5 Pro (똑똑함)
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={GEMINI_API_KEY}",
        # 3순위: 1.0 Pro (구형이지만 안정적)
        f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    ]
    
    headers = {'Content-Type': 'application/json'}
    prompt = f"""
    주제: '{topic}'
    위 주제에 대해 가장 흥미로운 TOP 10 랭킹을 작성해.
    형식: "순위. 항목명 - 핵심설명(20자 이내)"
    사족 금지. 오직 리스트만 출력.
    """
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    # 모델들을 순서대로 돌면서 접속 시도
    for url in urls:
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                # 성공하면 바로 리턴!
                return response.json()['candidates'][0]['content']['parts'][0]['text']
        except:
            continue # 실패하면 다음 모델로 조용히 넘어감

    # 🔥 모든 AI가 전화를 안 받으면? -> 비상용 원고 생성기 가동!
    return emergency_backup_generator(topic)

# --- 3. 🎨 이미지 생성 (디자인 공장) ---
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

    draw.rectangle([(0,0), (W, H)], outline=(255, 0, 0), width=15)
    draw.line([(0, 250), (W, 250)], fill=(255, 0, 0), width=5)

    para = textwrap.wrap(topic, width=16)
    current_h = 80
    for line in para:
        bbox = draw.textbbox((0, 0), line, font=font_title)
        text_w = bbox[2] - bbox[0]
        draw.text(((W - text_w) / 2, current_h), line, font=font_title, fill="white")
        current_h += 80

    draw.text((50, 270), "TOP 10 RANKING", font=font_sub, fill="gray")

    lines = text_content.strip().split('\n')
    start_y = 350
    gap = 90
    
    count = 0
    for line in lines:
        clean = line.strip()
        if not clean: continue
        
        # 숫자로 시작하는 줄만 그리기
        if clean[0].isdigit():
            count += 1
            if count > 10: break
            if len(clean) > 28: clean = clean[:28] + "..."
            color = (255, 215, 0) if count <= 3 else "white"
            draw.text((80, start_y), clean, font=font_list, fill=color)
            start_y += gap

    footer = "구독 🙏 좋아요 ❤️"
    bbox_foot = draw.textbbox((0, 0), footer, font=font_list)
    draw.text(((W - (bbox_foot[2] - bbox_foot[0]))/2, H - 100), footer, font=font_list, fill=(255, 100, 100))

    return img

# --- 4. 메인 화면 ---
st.set_page_config(page_title="무중단 AI 공장", page_icon="🛡️", layout="wide")
st.title("🛡️ 3호점: 절대 멈추지 않는 공장")

if 'result_text' not in st.session_state:
    st.session_state['result_text'] = ""
if 'img' not in st.session_state:
    st.session_state['img'] = None

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 주제 입력")
    topic = st.text_input("주제", value="2025년 대박 날 AI 관련주 TOP 10")
    
    # 버튼 하나로 끝
    if st.button("🚀 실행 (오류 시 비상 모드 자동 가동)", use_container_width=True, type="primary"):
        with st.spinner("AI 연결 시도 중... (실패하면 비상 모드로 전환됩니다)"):
            
            # AI에게 시도해보고, 안 되면 비상용 원고를 가져옴
            generated_text = direct_ai_generation(topic)
            
            # 화면에 표시
            st.session_state['result_text'] = generated_text
            
            # 이미지 생성
            st.session_state['img'] = create_ranking_image(topic, generated_text)
            
            st.success("생성 완료! 내용을 확인하세요.")

    # 편집창
    edited_text = st.text_area(
        "내용 수정 (AI가 쓴 게 맘에 안 들면 여기서 고치세요)", 
        value=st.session_state['result_text'],
        height=350
    )
    
    if st.button("🔄 수정한 내용으로 이미지 업데이트"):
        if edited_text:
            st.session_state['img'] = create_ranking_image(topic, edited_text)
            st.success("업데이트 완료!")

with col2:
    st.subheader("🖼️ 결과물")
    if st.session_state['img']:
        st.image(st.session_state['img'], caption="최종 결과", use_container_width=True)
        
        buf = io.BytesIO()
        st.session_state['img'].save(buf, format="PNG")
        st.download_button("💾 이미지 다운로드", buf.getvalue(), "result.png", "image/png", use_container_width=True)
    else:
        st.info("버튼을 누르면 결과가 나옵니다.")