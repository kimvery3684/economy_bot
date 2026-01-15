import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import os
import requests
from bs4 import BeautifulSoup
from io import BytesIO
import random
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip

# --- [1. 기본 설정 및 폴더 준비] ---
st.set_page_config(page_title="JJ 경제 쇼츠 자동공장", page_icon="🎬", layout="wide")

FONT_FILE = "NanumGothic-ExtraBold.ttf"
TEMP_DIR = "temp_files"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# --- [2. 바이럴 주제 30선] ---
VIRAL_QUESTIONS = [
    "외국인이 1주일 내내\n몰래 쓸어담은 종목 TOP 10",
    "기관이 손절하고\n외인이 갈아탄 의외의 종목",
    "연기금 형님들이 찜한\n'절대 망하지 않을' 주식",
    "AI 서버 증설 수혜,\n숨겨진 소부장 리스트",
    "엔비디아도 탐내는\nHBM 기술력 보유 기업 TOP 5",
    "로봇 테마주 중\n진짜 실적이 찍히는 종목",
    "15년 전 아반떼 가격 vs\n현재 아반떼 가격 (물가 체감)",
    "20년 전 삼성전자 100주\n샀다면 지금 얼마일까?",
    "비트코인 1만원일 때\n안 사고 산 것들 TOP 5",
    "매달 월세처럼 돈 들어오는\n'월배당' 꿀조합 리스트",
    "자녀에게 세금 없이\n물려주기 좋은 10년 장기주",
    "상장폐지 주의보!\n개미들 가장 많이 물린 위험주",
    "금리 인하 시작되면\n미친듯이 튀어오를 종목 TOP 5",
    "워렌 버핏이 한국 오면\n당장 매수할 저평가 종목",
    "현금 10억 부자들이\n포트폴리오에 꼭 넣는 종목",
    "물가 상승률 압살하는\n배당 성장주 TOP 10",
    "전 세계가 러브콜!\nK-방산 수출 대박 종목",
    "지금 당장 안 사면\n평생 후회할 주식 1위",
    "내일 당장 상한가\n직행할 차트 분석 종목",
    "부자들만 몰래 듣는\n금리 수혜주 리스트",
    "월급 300만원 개미가\n10억 만든 비결 종목은?",
    "자산가들이 경기 불황에\n현금을 금으로 바꾸는 이유",
    "자식에게 물려줄\n압도적 1등 기업 TOP 5",
    "2차전지 끝났다?\n다시 불붙을 대장주 분석",
    "코스피 떡락에도\n수급 대장 노릇 하는 종목",
    "대한민국 망한다?\n위기 속에 돈 버는 기업들",
    "가장 똑똑한 서학개미가\n매수한 미국 주식 TOP 10",
    "수익률 400% 넘긴\n전설의 한달 급등 종목",
    "작년에 샀으면 몇 배?\n로봇 테마주 수익률 랭킹",
    "돈이 몰리는 곳이 정답!\n실시간 거래대금 TOP 10"
]

# --- [3. 기능 함수들] ---
def get_live_stocks():
    try:
        url = "https://finance.naver.com/sise/sise_quant.naver"
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('table.type_2 tr')[2:]
        data = []
        for item in items:
            name_tag = item.select_one('a.tltle')
            if name_tag:
                name = name_tag.text
                rate_tag = item.select('td.number')[3].select_one('span')
                if rate_tag:
                    rate = ("+" if 'red' in str(rate_tag) else "-" if 'blue' in str(rate_tag) else "") + rate_tag.text.strip()
                    data.append(f"{name}, {rate}")
            if len(data) >= 10: break
        return "\n".join(data)
    except: return "데이터 로드 실패"

def get_font(size):
    return ImageFont.truetype(FONT_FILE, size) if os.path.exists(FONT_FILE) else ImageFont.load_default()

def create_image(data_list, d):
    canvas = Image.new('RGB', (1080, 1920), d['bg_color'])
    draw = ImageDraw.Draw(canvas)
    # 디자인 로직 (기존과 동일)
    draw.rectangle([(0, 0), (1080, d['top_h'])], fill=d['top_bg'])
    draw.text((540, (d['top_h']/2)+d['top_y_adj']), d['top_text'], font=get_font(d['top_fs']), fill=d['top_color'], anchor="mm", align="center", spacing=20)
    sub_y = d['top_h'] + 30
    draw.rectangle([(50, sub_y), (1030, sub_y + 100)], fill="#FFFF00")
    draw.text((540, sub_y + 50), d['sub_text'], font=get_font(50), fill="#000000", anchor="mm")
    start_y = sub_y + 180
    for i, line in enumerate(data_list):
        if i >= 10: break
        p = line.split(',')
        name, rate = p[0].strip(), p[1].strip() if len(p)>1 else ""
        cur_y = start_y + (i * d['row_h'])
        if i % 2 == 0: draw.rectangle([(50, cur_y - 50), (1030, cur_y + 50)], fill="#1A1A1A")
        draw.text((120, cur_y), f"{i+1}", font=get_font(d['item_fs']), fill="#FFFFFF", anchor="mm")
        draw.text((250, cur_y), name, font=get_font(d['item_fs']), fill="#FFFFFF", anchor="lm")
        color = "#FF3333" if "+" in rate else "#3388FF" if "-" in rate else "#FFFFFF"
        draw.text((950, cur_y), rate, font=get_font(d['item_fs']), fill=color, anchor="rm")
    draw.rectangle([(0, 1920-250), (1080, 1920)], fill="#000000")
    draw.text((540, 1920-125), d['bot_text'], font=get_font(45), fill="#FFFF00", anchor="mm", align="center")
    return canvas

# --- [4. 영상 제작 엔진 (핵심 신기능)] ---
def make_video(image, text):
    img_path = os.path.join(TEMP_DIR, "frame.jpg")
    audio_path = os.path.join(TEMP_DIR, "voice.mp3")
    output_path = os.path.join(TEMP_DIR, "shorts_output.mp4")
    
    # 1. 이미지 임시 저장
    image.save(img_path)
    
    # 2. AI 음성 생성 (TTS)
    tts = gTTS(text=text.replace("\n", " "), lang='ko')
    tts.save(audio_path)
    
    # 3. 비디오 클립 생성 (기본 8초)
    audio = AudioFileClip(audio_path)
    duration = max(8, audio.duration + 1) # 음성 길이에 맞춤
    
    clip = ImageClip(img_path).set_duration(duration)
    clip = clip.set_audio(audio)
    
    # 4. 파일 출력 (속도를 위해 오디오 코덱 지정)
    clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    return output_path

# --- [5. UI] ---
st.title("💰 3호점: 경제 쇼츠 자동 완성 공장")
col_L, col_R = st.columns([1, 1.2])

with col_L:
    with st.container(border=True):
        st.subheader("1. 콘텐츠 자동 생성")
        if st.button("🎲 랜덤 주제 & 실시간 데이터 동기화", type="primary", use_container_width=True):
            st.session_state.q = random.choice(VIRAL_QUESTIONS)
            st.session_state.d = get_live_stocks()
        
        top_text = st.text_area("제목", st.session_state.get('q', VIRAL_QUESTIONS[0]), height=100)
        data_input = st.text_area("데이터", st.session_state.get('d', ""), height=150)
        data_list = [l.strip() for l in data_input.split('\n') if l.strip()]

    with st.expander("2. 디자인 조절 (최적값 고정)"):
        top_h = st.slider("높이", 100, 600, 400)
        top_fs = st.slider("글자", 20, 150, 103)
        top_y_adj = st.slider("위치", -200, 200, 66)
        row_h = st.slider("간격", 50, 250, 120)
        item_fs = st.slider("리스트", 20, 100, 55)

    design = {'bg_color': "#000000", 'top_text': top_text, 'top_h': top_h, 'top_fs': top_fs, 'top_lh': 20, 'top_y_adj': top_y_adj, 'top_bg': "#FFFF00", 'top_color': "#000000", 'sub_text': "실시간 거래대금 TOP 10", 'row_h': row_h, 'item_fs': item_fs, 'bot_text': "인물을 두번 톡톡 누르고,\n댓글 남겨주세요!!"}

with col_R:
    st.subheader("🖼️ 미리보기 & 영상 제작")
    if data_list:
        final_img = create_image(data_list, design)
        st.image(final_img, use_container_width=True)
        
        st.write("---")
        if st.button("🎬 MP4 영상 파일로 만들기 (AI 음성 포함)", use_container_width=True):
            with st.spinner("영상 제작 중... (약 10~20초 소요)"):
                video_file = make_video(final_img, top_text)
                with open(video_file, "rb") as f:
                    st.download_button("💾 완성된 영상 다운로드 (.mp4)", f, "economy_shorts.mp4", "video/mp4", use_container_width=True)
                st.success("영상 제작 완료!")