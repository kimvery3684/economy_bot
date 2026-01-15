import streamlit as st
import json
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import google.generativeai as genai
from duckduckgo_search import DDGS  # 👈 구글급 성능의 무료 검색 도구

# ==========================================
# 👇 API 키 입력 (따옴표 필수!)
GEMINI_API_KEY = "AIzaSyC-QRPifVhQGIGCjxk2kKDC0htuyiG0fTk"
# ==========================================

# --- 1. 🌐 실시간 웹 검색 함수 (네이버 대신 구글/웹 검색) ---
def web_search(keyword):
    """DuckDuckGo를 통해 전 세계 웹 문서를 검색합니다."""
    try:
        # 검색어 뒤에 '최신 정보' 등을 붙여 정확도 높임
        search_query = f"{keyword} 최신 분석 정리"
        
        # 웹에서 상위 10개 결과 수집
        results = DDGS().text(search_query, max_results=10)
        return results
    except Exception as e:
        st.error(f"웹 검색 중 오류 발생: {e}")
        return None

# --- 2. 🤖 제미나이 분석 및 요약 ---
def get_gemini_response(topic, search_results):
    if len(GEMINI_API_KEY) < 10 or "여기에" in GEMINI_API_KEY:
        st.error("API 키를 입력해주세요!")
        return None

    # 검색된 데이터를 하나의 텍스트로 합침
    context = ""
    for item in search_results:
        title = item.get('title', '제목 없음')
        body = item.get('body', '내용 없음')
        context += f"출처: {title}\n내용: {body}\n\n"

    # 제미나이에게 내리는 '분석가' 모드 명령
    prompt = f"""
    너는 세계 최고의 경제 분석가야. 아래 수집된 '실시간 웹 검색 데이터'를 정밀 분석해서 '{topic}'에 대한 TOP 10 랭킹을 작성해.
    
    [분석 규칙]
    1. 블로그 광고글 말고, 뉴스나 전문 분석 자료를 우선적으로 반영해.
    2. 구체적인 종목명, 기업명, 아이템명을 명확하게 뽑아내.
    3. 데이터가 부족하면 너의 배경지식을 20% 정도 섞어서 완성도 있게 만들어.
    
    [출력 형식]
    반드시 아래 포맷만 출력해 (설명은 20자 내외로 짧고 강렬하게):
    1. 핵심이름 - 핵심설명
    2. 핵심이름 - 핵심설명
    ...
    
    [수집된 웹 데이터]
    {context}
    """

    genai.configure(api_key=GEMINI_API_KEY)

    # 모델 자동 우회 (에러 방지)
    models = ['gemini-1.5-flash', 'gemini-pro', 'gemini-1.0-pro']
    
    for model_name in models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text.strip()
        except:
            continue

    st.error("AI 연결 실패. 잠시 후 다시 시도해주세요.")
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

    # 빨간 테두리 디자인
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

    draw.text((50, 270), "Global Data Analysis", font=font_sub, fill="gray")

    # 내용 그리기
    lines = text_content.strip().split('\n')
    start_y = 350
    gap = 90
    
    count = 0
    for line in lines:
        clean_line = line.strip()
        if not clean_line: continue
        
        # 번호가 있는 줄만 처리 (1. 등)
        if len(clean_line) > 0 and clean_line[0].isdigit():
            count += 1
            if count > 10: break
            
            if len(clean_line) > 26: clean_line = clean_line[:26] + "..."
            
            # 1~3위 금색 강조
            color = (255, 215, 0) if count <= 3 else "white"
            draw.text((80, start_y), clean_line, font=font_list, fill=color)
            start_y += gap

    footer = "구독 🙏 좋아요 ❤️"
    bbox_foot = draw.textbbox((0, 0), footer, font=font_list)
    draw.text(((W - (bbox_foot[2] - bbox_foot[0]))/2, H - 100), footer, font=font_list, fill=(255, 100, 100))

    return img

# --- 4. 메인 화면 ---
st.set_page_config(page_title="글로벌 쇼츠 공장", page_icon="🌍", layout="wide")
st.title("🌍 3호점: 글로벌 데이터 쇼츠 공장")

if 'draft' not in st.session_state:
    st.session_state['draft'] = ""
if 'img' not in st.session_state:
    st.session_state['img'] = None

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 주제 입력 (구글/웹 데이터 기반)")
    topic = st.text_input("주제", value="2025년 글로벌 AI 트렌드 TOP 10")
    
    if st.button("🚀 웹 검색 + AI 분석 + 이미지 생성", use_container_width=True, type="primary"):
        with st.spinner("구글(웹)에서 최신 정보를 수집하고 분석 중입니다..."):
            # 1. 웹 검색 (DuckDuckGo)
            search_data = web_search(topic)
            
            if search_data:
                # 2. 제미나이 분석
                ai_result = get_gemini_response(topic, search_data)
                
                if ai_result:
                    st.session_state['draft'] = ai_result
                    # 3. 이미지 생성
                    st.session_state['img'] = create_ranking_image(topic, ai_result)
                    st.success("분석 완료! 진짜 정보를 확인하세요.")
                else:
                    st.error("AI 연결 실패 (키를 확인하세요)")
            else:
                st.error("웹 검색 결과가 없습니다.")

    # 수정 공간
    edited_text = st.text_area(
        "내용 수정 (AI 분석 결과)", 
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
        st.download_button("💾 이미지 다운로드", buf.getvalue(), "global_ranking.png", "image/png", use_container_width=True)
    else:
        st.info("왼쪽 버튼을 누르면 전 세계 웹을 뒤져서 결과를 만듭니다.")