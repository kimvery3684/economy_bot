import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import google.generativeai as genai
from duckduckgo_search import DDGS # 무료 검색 도구

# ==========================================
# 👇 API 키 입력 (혹시 틀려도 작동하게 만들었습니다!)
GEMINI_API_KEY = "AIzaSyC-QRPifVhQGIGCjxk2kKDC0htuyiG0fTk"
# ==========================================

# --- 1. 🌐 검색 함수 (API 키 필요 없음, 무제한 무료) ---
def search_web(topic):
    """오류 없이 무조건 검색 결과를 가져오는 함수"""
    try:
        # 10개의 최신 결과 수집
        results = DDGS().text(f"{topic} 팩트 통계 순위", max_results=10)
        return results
    except Exception as e:
        st.error(f"검색 도구 오류: {e}")
        return []

# --- 2. 🤖 제미나이 요약 (실패하면 바로 포기하고 원본 사용) ---
def try_gemini_summary(topic, search_results):
    # 키가 없거나 이상하면 바로 포기 -> 원본 데이터 사용
    if len(GEMINI_API_KEY) < 10 or "여기에" in GEMINI_API_KEY:
        return None

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 검색 데이터 정리
        data_text = ""
        for item in search_results:
            data_text += f"- {item['title']}: {item['body']}\n"

        prompt = f"""
        주제: '{topic}'
        위 데이터를 바탕으로 TOP 10 리스트를 한글로 작성해.
        형식: "순위. 항목명 - 핵심설명(20자 이내)"
        사족 금지. 오직 리스트만 출력.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        # 🔥 에러가 나면 조용히 None을 반환하고 비상 모드로 전환
        return None

# --- 3. ⚡ 비상용 포맷터 (AI가 안 될 때 작동) ---
def fallback_formatter(search_results):
    """검색된 제목과 내용을 그대로 리스트로 만듦"""
    formatted_text = ""
    for i, item in enumerate(search_results, 1):
        title = item['title'].replace("...", "")
        # 제목이 너무 길면 자름
        if len(title) > 20: title = title[:20]
        formatted_text += f"{i}. {title} - 상세 내용 참조\n"
    return formatted_text

# --- 4. 🎨 이미지 생성 함수 ---
def create_image(topic, text_content):
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

    # 리스트 그리기
    lines = text_content.strip().split('\n')
    start_y = 350
    gap = 90
    
    count = 0
    for line in lines:
        clean = line.strip()
        if not clean: continue
        
        # 숫자(순위)로 시작하는지 확인
        if clean[0].isdigit():
            count += 1
            if count > 10: break # 최대 10개
            
            if len(clean) > 28: clean = clean[:28] + "..."
            
            color = (255, 215, 0) if count <= 3 else "white"
            draw.text((80, start_y), clean, font=font_list, fill=color)
            start_y += gap

    # 하단
    footer = "구독 🙏 좋아요 ❤️"
    bbox_foot = draw.textbbox((0, 0), footer, font=font_list)
    draw.text(((W - (bbox_foot[2] - bbox_foot[0]))/2, H - 100), footer, font=font_list, fill=(255, 100, 100))

    return img

# --- 5. 메인 화면 ---
st.set_page_config(page_title="무적의 쇼츠 공장", page_icon="🛡️", layout="wide")
st.title("🛡️ 3호점: 절대 멈추지 않는 공장")

if 'final_text' not in st.session_state:
    st.session_state['final_text'] = ""
if 'img' not in st.session_state:
    st.session_state['img'] = None

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 주제 입력")
    topic = st.text_input("주제", value="2025년 뜨는 기술 TOP 10")
    
    if st.button("🚀 실행 (실패 시 원본 데이터 출력)", use_container_width=True, type="primary"):
        with st.spinner("데이터를 찾는 중..."):
            # 1. 무조건 검색 (키 필요 없음)
            results = search_web(topic)
            
            if results:
                # 2. 제미나이에게 "한번 다듬어봐" 라고 시킴
                summary = try_gemini_summary(topic, results)
                
                if summary:
                    # 성공하면 예쁜 AI 요약본 사용
                    st.success("✅ AI 분석 성공!")
                    st.session_state['final_text'] = summary
                else:
                    # 실패하면 검색 결과 그대로 사용 (에러 없음!)
                    st.warning("⚠️ AI 연결 불안정 -> 검색 결과 원본을 표시합니다.")
                    st.session_state['final_text'] = fallback_formatter(results)
                
                # 3. 이미지 생성
                st.session_state['img'] = create_image(topic, st.session_state['final_text'])
            else:
                st.error("검색 결과가 없습니다.")

    # 텍스트 수정창
    edited_text = st.text_area(
        "내용 수정 (여기서 고치면 이미지에 반영됨)", 
        value=st.session_state['final_text'],
        height=400
    )
    
    if st.button("🔄 수정사항 반영"):
        if edited_text:
            st.session_state['img'] = create_image(topic, edited_text)
            st.success("반영 완료")

with col2:
    st.subheader("🖼️ 결과물")
    if st.session_state['img']:
        st.image(st.session_state['img'], caption="결과 이미지", use_container_width=True)
        
        buf = io.BytesIO()
        st.session_state['img'].save(buf, format="PNG")
        st.download_button("💾 다운로드", buf.getvalue(), "result.png", "image/png", use_container_width=True)