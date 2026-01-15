import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import os
import requests
from bs4 import BeautifulSoup
from io import BytesIO
import random
# 서버 환경에 따라 ImageMagick 설정 (moviepy 에러 방지)
from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"}) 
from moviepy.editor import ImageClip, AudioFileClip
from gtts import gTTS

# --- [1. 기본 설정] ---
st.set_page_config(page_title="JJ 경제 쇼츠 만능공장", page_icon="🏭", layout="wide")
FONT_FILE = "NanumGothic-ExtraBold.ttf"
TEMP_DIR = "temp_files"
if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)

# --- [2. 조회수 폭발 주제 (카테고리별 분류)] ---
TOPICS = {
    "🔥 급등/수급": [
        "오늘 당장 상한가!\n실시간 급등 종목 TOP 10",
        "외국인이 미친듯이\n쓸어담는 종목 TOP 10",
        "돈이 몰리는 곳이 정답\n거래대금 폭발 TOP 10"
    ],
    "👑 시가총액/대장주": [
        "대한민국을 움직이는\n코스피 시가총액 TOP 10",
        "망할 일 없는 기업\n코스닥 우량주 TOP 10",
        "지금 사서 묻어두면\n부자되는 대장주 TOP 10"
    ],
    "💰 배당/가치주": [
        "은행 이자보다 낫다!\n고배당 수익률 TOP 10",
        "저평가 우량주\nPER 낮은 순위 TOP 10",
        "외국인 지분율 높은\n알짜배기 품절주 TOP 10"
    ]
}

# --- [3. 만능 데이터 수집 엔진] ---
def get_naver_data(mode):
    try:
        # 1. 모드별 URL 및 설정
        if mode == "🔥 급등/수급":
            url = "https://finance.naver.com/sise/sise_quant.naver" # 거래량 상위
            col_idx = 3 # 등락률 위치
        elif mode == "👑 시가총액/대장주":
            url = "https://finance.naver.com/sise/sise_market_sum.naver" # 시총 상위
            col_idx = 4 # 등락률 위치
        elif mode == "💰 배당/가치주":
            url = "https://finance.naver.com/sise/sise_dividend.naver" # 배당 수익률
            col_idx = 3 # (배당 페이지는 구조가 다를 수 있어 기본값 설정)
            
        session = requests.Session()
        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.naver.com/'}
        res = session.get(url, headers=headers)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')

        # 2. 데이터 추출 로직
        data = []
        table = soup.select_one('table.type_2')
        if not table: return "데이터 테이블 없음"
        
        rows = table.select('tr')
        for row in rows:
            # 종목명 찾기
            name_tag = row.select_one('a.tltle')
            if not name_tag: name_tag = row.select_one('a.title') # 페이지마다 클래스명이 다를 수 있음
            
            if name_tag:
                name = name_tag.text.strip()
                
                # 수치 찾기 (등락률 or 현재가 or 배당수익률)
                tds = row.select('td.number')
                if len(tds) > col_idx:
                    # 배당주는 '수익률'을 가져오고, 나머지는 '등락률'을 가져옴
                    if mode == "💰 배당/가치주":
                         # 배당 페이지는 구조가 복잡하여 예외적으로 6번째 칸(수익률) 추출 시도
                         val = tds[6].text.strip() if len(tds) > 6 else ""
                         final_val = f"+{val}%" if val else "정보없음"
                    else:
                        # 일반 등락률
                        span = tds[col_idx].select_one('span')
                        if span:
                            txt = span.text.strip()
                            cls = span.get('class', [])
                            prefix = "+" if 'red02' in cls else "-" if 'blue02' in cls else ""
                            final_val = prefix + txt
                        else:
                            final_val = "0.00%"
                    
                    data.append(f"{name}, {final_val}")
            
            if len(data) >= 10: break
            
        return "\n".join(data) if data else "데이터 수집 실패"

    except Exception as e:
        return f"에러 발생: {e}"

# --- [4. 이미지/영상 엔진 (기존 유지)] ---
def get_font(size):
    return ImageFont.truetype(FONT_FILE, size) if os.path.exists(FONT_FILE) else ImageFont.load_default()

def create_image(data_list, d):
    canvas = Image.new('RGB', (1080, 1920), d['bg_color'])
    draw = ImageDraw.Draw(canvas)
    
    # 상단
    draw.rectangle([(0, 0), (1080, d['top_h'])], fill=d['top_bg'])
    draw.text((540, (d['top_h']/2)+d['top_y_adj']), d['top_text'], font=get_font(d['top_fs']), fill=d['top_color'], anchor="mm", align="center", spacing=20)
    
    # 소제목
    sub_y = d['top_h'] + 30
    draw.rectangle([(50, sub_y), (1030, sub_y + 100)], fill="#FFFF00")
    draw.text((540, sub_y + 50), d['sub_text'], font=get_font(50), fill="#000000", anchor="mm")
    
    # 리스트
    start_y = sub_y + 180
    for i, line in enumerate(data_list):
        if i >= 10: break
        p = line.split(',')
        if len(p) < 2: continue
        name, val = p[0].strip(), p[1].strip()
        
        cur_y = start_y + (i * d['row_h'])
        if i % 2 == 0: draw.rectangle([(50, cur_y - 50), (1030, cur_y + 50)], fill="#1A1A1A")
        
        draw.text((120, cur_y), f"{i+1}", font=get_font(d['item_fs']), fill="#FFFFFF", anchor="mm")
        draw.text((250, cur_y), name, font=get_font(d['item_fs']), fill="#FFFFFF", anchor="lm")
        
        # 색상 로직: +는 빨강, -는 파랑, 나머지는 흰색
        color = "#FF3333" if "+" in val else "#3388FF" if "-" in val else "#FFFFFF"
        draw.text((950, cur_y), val, font=get_font(d['item_fs']), fill=color, anchor="rm")
        
    # 하단
    draw.rectangle([(0, 1920-250), (1080, 1920)], fill="#000000")
    draw.text((540, 1920-125), d['bot_text'], font=get_font(45), fill="#FFFF00", anchor="mm", align="center")
    return canvas

def make_video(image, text):
    img_path = os.path.join(TEMP_DIR, "frame.jpg")
    audio_path = os.path.join(TEMP_DIR, "voice.mp3")
    output_path = os.path.join(TEMP_DIR, "shorts_output.mp4")
    image.save(img_path)
    tts = gTTS(text=text.replace("\n", " "), lang='ko')
    tts.save(audio_path)
    audio = AudioFileClip(audio_path)
    clip = ImageClip(img_path).set_duration(max(8, audio.duration + 1)).set_audio(audio)
    clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    return output_path

# --- [5. UI 메인] ---
st.title("🏭 3호점: 주제별 자동 생산 공장")
col_L, col_R = st.columns([1, 1.2])

if 'q' not in st.session_state: st.session_state.q = TOPICS["🔥 급등/수급"][0]
if 'd' not in st.session_state: st.session_state.d = ""
if 'cat' not in st.session_state: st.session_state.cat = "🔥 급등/수급"

with col_L:
    st.header("1. 주제 선택 & 데이터 추출")
    
    # 카테고리 선택 탭
    tabs = st.tabs(TOPICS.keys())
    for i, category in enumerate(TOPICS.keys()):
        with tabs[i]:
            if st.button(f"🚀 '{category}' 데이터 가져오기", key=f"btn_{i}", use_container_width=True):
                st.session_state.cat = category
                st.session_state.q = random.choice(TOPICS[category])
                with st.spinner(f"네이버에서 '{category}' 정보 긁어오는 중..."):
                    st.session_state.d = get_naver_data(category)
                st.success("완료!")

    # 편집 영역
    with st.container(border=True):
        top_text = st.text_area("제목 (수정 가능)", st.session_state.q, height=80)
        data_input = st.text_area("추출된 데이터 (종목명, 수치)", st.session_state.d, height=200)
        
        # 소제목 자동 변경 로직
        default_sub = "실시간 순위 TOP 10"
        if "배당" in st.session_state.cat: default_sub = "배당 수익률 순위"
        elif "시가총액" in st.session_state.cat: default_sub = "시가총액 순위"
        
        sub_text = st.text_input("소제목(노란바)", default_sub)
        data_list = [l.strip() for l in data_input.split('\n') if l.strip()]

    # 디자인
    with st.expander("🎨 디자인 조절"):
        top_h = st.slider("높이", 100, 600, 400)
        top_fs = st.slider("글자", 20, 150, 103)
        top_y_adj = st.slider("위치", -200, 200, 66)
        row_h = st.slider("간격", 50, 250, 120)
        item_fs = st.slider("리스트", 20, 100, 55)

    design = {'bg_color': "#000000", 'top_text': top_text, 'top_h': top_h, 'top_fs': top_fs, 'top_lh': 20, 'top_y_adj': top_y_adj, 'top_bg': "#FFFF00", 'top_color': "#000000", 'sub_text': sub_text, 'row_h': row_h, 'item_fs': item_fs, 'bot_text': "구독과 좋아요를 누르면\n자산이 2배로 늘어납니다!"}

with col_R:
    st.subheader("🖼️ 미리보기 & 영상 제작")
    if data_list and "실패" not in data_list[0]:
        final_img = create_image(data_list, design)
        st.image(final_img, use_container_width=True)
        st.write("---")
        if st.button("🎬 MP4 영상 파일로 만들기", use_container_width=True):
            with st.spinner("영상 제작 중..."):
                video_file = make_video(final_img, top_text)
                with open(video_file, "rb") as f:
                    st.download_button("💾 완성된 영상 다운로드", f, "economy_shorts.mp4", "video/mp4", use_container_width=True)
    else:
        st.info("좌측에서 주제를 선택하고 데이터를 가져오세요.")