import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import google.generativeai as genai

# ==========================================
# 👇 [필수] 제미나이 API 키를 여기에 붙여넣으세요! (따옴표 필수)
GEMINI_API_KEY = "AIzaSyC-QRPifVhQGIGCjxk2kKDC0htuyiG0fTk"
# ==========================================

# --- 1. 🧠 제미나이 순수 창작 함수 (팩트 검증 프롬프트 탑재) ---
def generate_pure_content(topic):
    if len(GEMINI_API_KEY) < 10 or "여기에" in GEMINI_API_KEY:
        st.error("🚨 API 키가 입력되지 않았습니다. 코드 상단을 확인해주세요.")
        return None

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # 🔥 [핵심] 사장님이 지시하신 '팩트 체크' 명령어를 강력하게 입력
        prompt = f"""
        너는 데이터에 집착하는 '팩트 폭격기' 유튜브 쇼츠 작가야.
        주제: '{topic}'
        
        위 주제로 TOP 10 랭킹을 작성하되, 아래 **[엄격한 검증 규칙]**을 헌법처럼 지켜라.
        
        [🚫 검증 및 선정 기준 (절대 준수)]
        1. **객관적 사실(Fact) 원칙**: 구글/위키피디아/국제 언론/공식 통계 자료 등에서 교차 검증된 정보만 사용해.
        2. **출처 제한**: 출처가 불분명하거나, 주장에 가까운 정보, 개인 블로그/커뮤니티 썰은 절대 제외해.
        3. **명확한 정의**: 기준이 명확한 수치, 연도, 기록, 공식 명칭으로 딱 떨어지는 항목만 선정해.
        4. **선정 성격 (아래 중 하나 필수)**:
           - 숫자로 명확히 비교 가능한 극단성 (면적, 높이, 길이, 금액, 인원 수 등)
           - 공식 기록이나 랭킹이 존재하는 항목
        
        [✍️ 작성 포맷]
        아래 형식을 토씨 하나 틀리지 말고 지켜. (인사말/사족 금지)
        
        1. 순위 및 명칭 - 핵심설명 (20자 이내)
           (객관적 근거: 정확한 수치 또는 공식 기록 요약 1줄)
        
        2. 순위 및 명칭 - 핵심설명 (20자 이내)
           (객관적 근거: 정확한 수치 또는 공식 기록 요약 1줄)
        
        ... (10위까지 작성)
        """

        models = ['gemini-1.5-flash', 'gemini-pro', 'gemini-1.0-pro']
        
        for model_name in models:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return response.text.strip()
            except:
                continue

        st.error("AI 연결 실패. (API 키 오류 또는 구글 서버 문제)")
        return None

    except Exception as e:
        st.error(f"오류 발생: {e}")
        return None

# --- 2. 🎨 이미지 생성 함수 (근거 데이터 추가 표시) ---
def create_ranking_image(topic, text_content):
    W, H = 1080, 1350 
    img = Image.new('RGB', (W, H), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 70) 
        font_list = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 40)
        font_sub = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 30)
        font_desc = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 25) # 근거용 작은 폰트
    except:
        font_title = ImageFont.load_default()
        font_list = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_desc = ImageFont.load_default()

    # 디자인
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

    draw.text((50, 270), "OFFICIAL DATA RANKING", font=font_sub, fill="gray")

    # 리스트 그리기
    lines = text_content.strip().split('\n')
    start_y = 350
    
    # 랭킹 항목(큰 글씨)과 근거(작은 글씨)를 구분해서 그림
    count = 0
    for line in lines:
        clean_line = line.strip()
        if not clean_line: continue
        
        # 1. 랭킹 항목 (숫자로 시작하는 줄)
        if clean_line[0].isdigit() and "." in clean_line[:4]:
            count += 1
            if count > 10: break
            
            # 너무 길면 자르기
            if len(clean_line) > 28: clean_line = clean_line[:28] + "..."
            
            color = (255, 215, 0) if count <= 3 else "white"
            draw.text((80, start_y), clean_line, font=font_list, fill=color)
            start_y += 60 # 간격 조금 벌림

        # 2. 객관적 근거 (괄호로 시작하거나 '근거:' 가 있는 줄)
        elif clean_line.startswith("(") or "근거" in clean_line:
            draw.text((100, start_y), clean_line, font=font_desc, fill=(200, 200, 200)) # 회색
            start_y += 50 # 다음 항목으로 넘어가는 간격

    footer = "구독 🙏 좋아요 ❤️"
    bbox_foot = draw.textbbox((0, 0), footer, font=font_list)
    draw.text(((W - (bbox_foot[2] - bbox_foot[0]))/2, H - 100), footer, font=font_list, fill=(255, 100, 100))

    return img

# --- 3. 메인 화면 ---
st.set_page_config(page_title="팩트체크 쇼츠 공장", page_icon="⚖️", layout="wide")
st.title("⚖️ 3호점: 팩트체크 쇼츠 공장")

if 'draft' not in st.session_state:
    st.session_state['draft'] = ""
if 'img' not in st.session_state:
    st.session_state['img'] = None

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 주제 입력 (검증된 데이터)")
    topic = st.text_input("주제", value="세계에서 가장 비싼 기업 TOP 10")
    
    if st.button("🔍 팩트 기반 분석 + 이미지 생성", use_container_width=True, type="primary"):
        with st.spinner("제미나이가 전 세계 통계와 기록을 검증 중입니다..."):
            ai_result = generate_pure_content(topic)
            
            if ai_result:
                st.session_state['draft'] = ai_result
                st.session_state['img'] = create_ranking_image(topic, ai_result)
                st.success("검증 완료!")
            else:
                pass # 에러는 위에서 출력됨

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
    else:
        st.info("왼쪽 버튼을 누르면 '객관적 수치'가 포함된 랭킹이 나옵니다.")