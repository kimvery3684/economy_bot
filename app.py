import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import requests
from bs4 import BeautifulSoup

# --- 메인 화면 설정 ---
st.set_page_config(page_title="큰손 수급 추적기", page_icon="💸", layout="wide")
st.title("💸 3호점: 외국인/기관 순매수 TOP 10")

# --- 1. 네이버 금융 '투자자별 순매수' 크롤링 ---
def get_investor_rank(investor_type):
    """
    네이버 금융에서 외국인/기관 순매수 상위 종목을 긁어옵니다.
    investor_type: '9000'(외국인) 또는 '1000'(기관)
    """
    url = f"https://finance.naver.com/sise/sise_deal_rank.naver?investor_gubun={investor_type}"
    
    try:
        response = requests.get(url)
        response.encoding = 'euc-kr' # 한글 깨짐 방지
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 순매수 테이블 찾기
        tables = soup.find_all('table', {'class': 'type_2'})
        if not tables:
            return None
            
        # 보통 첫번째 테이블이 코스피, 두번째가 코스닥 등임. 여기선 '코스피' 기준(첫번째)
        target_table = tables[0]
        rows = target_table.find_all('tr')
        
        data_list = []
        count = 0
        
        for row in rows:
            cols = row.find_all('td')
            # 유효한 데이터 행인지 확인 (순위가 있는 행)
            if len(cols) > 3 and cols[0].get_text(strip=True).isdigit():
                rank = cols[0].get_text(strip=True)
                name = cols[1].get_text(strip=True)
                # 순매수 대금 (단위: 억 등 사이트 기준) - 보통 3번째 칸이 가격, 4~5번째가 순매수량 등 변동 가능
                # 네이버 '순매수 상위' 페이지 기준: [순위, 종목명, 현재가, 전일비, 등락률, 순매수량(추정)]
                # 정확한 금액 데이터 추출
                amount = cols[5].get_text(strip=True) # 순매수량/금액
                
                data_list.append((rank, name, amount))
                count += 1
                if count == 10:
                    break
                    
        return data_list

    except Exception as e:
        return []

# --- 2. 🎨 이미지 생성 (검은색 배경 + 전문가 스타일 테이블) ---
def create_dark_table_image(title, data_list):
    W, H = 1080, 1350 
    # 1. 배경: 완전 검은색 (전문가 느낌)
    img = Image.new('RGB', (W, H), color=(10, 10, 10)) 
    draw = ImageDraw.Draw(img)

    try:
        # 폰트 로드 (굵은 고딕체 필수)
        font_header = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 70) 
        font_col_head = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 40)
        font_row = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 45)
        font_rank = ImageFont.truetype("NanumGothic-ExtraBold.ttf", 50)
    except:
        font_header = ImageFont.load_default()
        font_col_head = ImageFont.load_default()
        font_row = ImageFont.load_default()
        font_rank = ImageFont.load_default()

    # 2. 상단 헤더 디자인
    # 빨간색/파란색 포인트 선
    draw.rectangle([(0, 0), (W, 250)], fill=(20, 20, 20)) # 상단 박스
    draw.line([(50, 240), (W-50, 240)], fill=(255, 50, 50), width=5) # 빨간 줄

    # 제목 표시
    bbox = draw.textbbox((0, 0), title, font=font_header)
    text_w = bbox[2] - bbox[0]
    draw.text(((W - text_w) / 2, 80), title, font=font_header, fill="white")

    # 3. 테이블 컬럼명 (순위 | 종목명 | 순매수)
    start_y = 300
    # 컬럼 배경
    draw.rectangle([(50, start_y), (W-50, start_y+80)], fill=(50, 50, 50))
    
    draw.text((100, start_y+15), "순위", font=font_col_head, fill=(200, 200, 200))
    draw.text((350, start_y+15), "종목명", font=font_col_head, fill=(200, 200, 200))
    draw.text((800, start_y+15), "순매수(주/금액)", font=font_col_head, fill=(200, 200, 200))

    # 4. 데이터 리스트 그리기
    current_y = 400
    gap = 90
    
    for rank, name, amount in data_list:
        # 순위 (노란색 강조)
        draw.text((110, current_y), rank, font=font_rank, fill=(255, 215, 0))
        
        # 종목명 (흰색)
        draw.text((350, current_y), name, font=font_row, fill="white")
        
        # 순매수량 (빨간색 = 매수 우위 상징)
        draw.text((800, current_y), amount, font=font_row, fill=(255, 80, 80))
        
        # 밑줄 (얇은 회색)
        draw.line([(50, current_y + 70), (W-50, current_y + 70)], fill=(50, 50, 50), width=2)
        
        current_y += gap

    # 5. 하단 워터마크
    footer = "구독 & 좋아요 ❤️"
    bbox_foot = draw.textbbox((0, 0), footer, font=font_col_head)
    draw.text(((W - (bbox_foot[2] - bbox_foot[0]))/2, H - 150), footer, font=font_col_head, fill="white")

    return img

# --- 3. 메인 화면 로직 ---
if 'img' not in st.session_state:
    st.session_state['img'] = None

col1, col2 = st.columns([1, 1])

with col1:
    st.header("🔍 데이터 선택")
    st.info("AI가 아니라 '네이버 금융' 실데이터를 긁어옵니다.")
    
    # 선택 상자 (외국인 vs 기관)
    option = st.selectbox(
        "누구의 장바구니를 훔쳐볼까요?",
        ("외국인 순매수 TOP 10", "기관 순매수 TOP 10")
    )
    
    if st.button("🚀 데이터 수집 및 표 생성", use_container_width=True, type="primary"):
        with st.spinner("네이버 금융에 접속해서 데이터를 가져오는 중..."):
            
            # 네이버 파라미터 설정
            if "외국인" in option:
                code = "9000" # 외국인 코드
                title_text = "외국인 순매수 TOP 10"
            else:
                code = "1000" # 기관 코드
                title_text = "기관 순매수 TOP 10"
                
            # 1. 크롤링
            rank_data = get_investor_rank(code)
            
            if rank_data:
                # 2. 이미지 생성
                st.session_state['img'] = create_dark_table_image(title_text, rank_data)
                st.success("생성 완료! 오른쪽을 확인하세요.")
            else:
                st.error("데이터를 가져오지 못했습니다. 장 운영 시간이 아닐 수 있습니다.")

with col2:
    st.subheader("🖼️ 완성된 디자인")
    if st.session_state['img']:
        st.image(st.session_state['img'], caption="최종 결과물", use_container_width=True)
        
        buf = io.BytesIO()
        st.session_state['img'].save(buf, format="PNG")
        st.download_button("💾 이미지 저장", buf.getvalue(), "investor_ranking.png", "image/png", use_container_width=True)
    else:
        st.info("왼쪽에서 버튼을 누르면 표가 만들어집니다.")