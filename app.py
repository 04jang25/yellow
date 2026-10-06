import streamlit as st
import cv2
import numpy as np
import pandas as pd
from datetime import datetime
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(
    page_title="열화상 타일 정밀 충진율 분석 시스템",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
    <style>
        html, body, [class*="css"] { font-size: 1.2rem !important; }
        .stApp { background-color: #f8fafc; color: #0f172a; }
        .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; max-width: 95% !important; }
        .title-card {
            background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
            padding: 1.5rem 2rem;
            border-radius: 14px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.12);
            margin-bottom: 1.5rem;
        }
        .title-card h1 { color: #ffffff !important; font-size: 2.2rem !important; font-weight: 800 !important; margin: 0 !important; }
        .title-card p { color: #dbeafe !important; font-size: 1.15rem !important; margin-top: 0.5rem !important; }
        .sub-instruction {
            background-color: #ffffff;
            padding: 1rem 1.2rem;
            border-radius: 10px;
            border-left: 6px solid #2563eb;
            font-weight: 700;
            color: #1e293b;
            font-size: 1.3rem !important;
            margin-bottom: 1.2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .stButton>button {
            font-size: 1.2rem !important;
            font-weight: 700 !important;
            padding: 0.7rem 1.5rem !important;
            border-radius: 8px !important;
        }
        h5 {
            font-size: 1.4rem !important;
            font-weight: 700 !important;
            color: #1e293b !important;
            margin-bottom: 0.8rem !important;
        }
        h3, .stSubheader { font-size: 1.6rem !important; font-weight: 800 !important; }
        [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e2e8f0 !important; }
        [data-testid="column"] { background: #ffffff; padding: 1.2rem; border-radius: 12px; border: 1px solid #cbd5e1; }
    </style>
""", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []
if "pts" not in st.session_state:
    st.session_state.pts = []
if "coord_key" not in st.session_state:
    st.session_state.coord_key = 0

st.markdown("""
    <div class="title-card">
        <h1>🔥 열화상 타일 정밀 충진율 분석 시스템</h1>
        <p>색상 범주별 고정 가중치(초록 100% / 노랑·주황 70% / 빨강 0%) 기반 분석 솔루션</p>
    </div>
""", unsafe_allow_html=True)

st.sidebar.header("📁 이미지 업로드")
uploaded_file = st.sidebar.file_uploader("열화상 사진 선택", type=["jpg", "jpeg", "png", "bmp"])

st.sidebar.markdown("---")
st.sidebar.info("💡 **마스크 명암 및 가중치 기준**\n\n- ⚪ **완전 충진(초록)**: 흰색 (100% 반영)\n- 🔘 **부분 충진(노랑/주황)**: 회색 (70% 반영)\n- ⚫ **미충진(빨강/빛반사)**: 검은색 (0% 반영)")

if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    full_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    if full_img is None:
        st.error("❌ 이미지를 불러올 수 없습니다.")
    else:
        orig_img = full_img
        img_h, img_w = orig_img.shape[:2]
        
        st.markdown('<div class="sub-instruction">📌 <b>RGB 타일 영역 4개 모서리 클릭:</b> 1.좌상 ➔ 2.우상 ➔ 3.우하 ➔ 4.좌하</div>', unsafe_allow_html=True)
        
        MAX_W = 400
        if img_w > MAX_W:
            canvas_w = MAX_W
            canvas_h = int(img_h * (MAX_W / img_w))
        else:
            canvas_w = img_w
            canvas_h = img_h
        
        bg_img_rgb = cv2.cvtColor(orig_img, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(bg_img_rgb).resize((canvas_w, canvas_h))
        
        draw_img = np.array(pil_image).copy()
        for i, p in enumerate(st.session_state.pts):
            cv2.circle(draw_img, (p[0], p[1]), 8, (255, 255, 255), -1)
            cv2.circle(draw_img, (p[0], p[1]), 6, (239, 68, 68), -1)
            cv2.putText(draw_img, str(i+1), (p[0]+12, p[1]+6), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            cv2.putText(draw_img, str(i+1), (p[0]+12, p[1]+6), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            st.markdown("##### 1. RGB 타일 (영역 지정)")
            value = streamlit_image_coordinates(
                Image.fromarray(draw_img),
                key=f"mobile_coord_{st.session_state.coord_key}"
            )

            if value is not None:
                point = [value["x"], value["y"]]
                if len(st.session_state.pts) < 4 and point not in st.session_state.pts:
                    st.session_state.pts.append(point)
                    st.rerun()

            col_btn1, col_btn2 = st.columns([1, 1])
            with col_btn1:
                st.write(f"📍 좌표 선택: **{len(st.session_state.pts)} / 4**")
                if st.button("🔄 리셋", use_container_width=True):
                    st.session_state.pts = []
                    st.session_state.coord_key += 1
                    st.rerun()
                    
            with col_btn2:
                run_btn = st.button("🚀 분석 실행", disabled=(len(st.session_state.pts) != 4), type="primary", use_container_width=True)

        if run_btn and len(st.session_state.pts) == 4:
            clicked_pts = []
            x_scale = img_w / canvas_w
            y_scale = img_h / canvas_h
            for pt in st.session_state.pts:
                clicked_pts.append([int(pt[0] * x_scale), int(pt[1] * y_scale)])

            src_pts = np.float32(clicked_pts)
            TARGET_W, TARGET_H = 600, 300
            dst_pts = np.float32([[0, 0], [TARGET_W, 0], [TARGET_W, TARGET_H], [0, TARGET_H]])
            
            matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
            warped_img = cv2.warpPerspective(orig_img, matrix, (TARGET_W, TARGET_H))
            warped_rgb = cv2.cvtColor(warped_img, cv2.COLOR_BGR2RGB)
            
            # HSV 변환
            hsv = cv2.cvtColor(warped_img, cv2.COLOR_BGR2HSV)
            
            # 1. 초록색 영역 (Hue 18~98)
            mask_green = cv2.inRange(hsv, np.array([18, 20, 20]), np.array([98, 255, 255]))

            # 2. 노란색~주황색 영역 (Hue 8~17)
            mask_yellow_orange = cv2.inRange(hsv, np.array([8, 20, 20]), np.array([17, 255, 255]))

            # 초록색 영역 우선 적용 (중복 제거)
            mask_yellow_orange = cv2.bitwise_and(mask_yellow_orange, cv2.bitwise_not(mask_green))

            # 모폴로지 연산 (노이즈 제거)
            kernel = np.ones((3, 3), np.uint8)
            mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_OPEN, kernel)
            mask_yellow_orange = cv2.morphologyEx(mask_yellow_orange, cv2.MORPH_OPEN, kernel)

            # 자잘한 노이즈 제거 (최소 크기 20픽셀 이상만 인정)
            num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask_yellow_orange)
            filtered_yellow = np.zeros_like(mask_yellow_orange)
            for i in range(1, num_labels):
                if stats[i, cv2.CC_STAT_AREA] >= 20:
                    filtered_yellow[labels == i] = 255
            mask_yellow_orange = filtered_yellow

            # 무채색 진단 마스크 생성 (회색: 128, 흰색: 255)
            display_mask_gray = np.zeros((TARGET_H, TARGET_W), dtype=np.uint8)
            display_mask_gray[mask_yellow_orange == 255] = 128  # 회색
            display_mask_gray[mask_green == 255] = 255          # 흰색

            # 픽셀 수 및 비율 계산
            green_pixels = np.sum(mask_green == 255)
            yellow_orange_pixels = np.sum(mask_yellow_orange == 255)
            total_pixels = TARGET_W * TARGET_H
            red_pixels = total_pixels - (green_pixels + yellow_orange_pixels)

            green_pct = (green_pixels / total_pixels) * 100.0
            yellow_orange_pct = (yellow_orange_pixels / total_pixels) * 100.0
            red_pct = max((red_pixels / total_pixels) * 100.0, 0.0)

            # 고정 가중치 70% 적용
            final_ratio = min(green_pct + (yellow_orange_pct * 0.70), 100.0)

            with col2:
                st.markdown("##### 2. 정면 보정")
                st.image(warped_rgb, use_container_width=True)
            
            with col3:
                st.markdown("##### 3. 진단 마스크 (Grayscale)")
                st.image(display_mask_gray, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)
            
            st.info("💡 **진단 마스크 톤 분석:** ⚪ **흰색(완전 충진)**: 100% | 🔘 **회색(부분 충진)**: 70% | ⚫ **검은색(미충진/빛반사)**: 0%")
            st.write(f"⚪ **흰색 (100%):** {green_pct:.2f}% | 🔘 **회색 (70%):** {yellow_orange_pct:.2f}% | ⚫ **검은색 (0%):** {red_pct:.2f}%")

            if final_ratio >= 80.0:
                st.success(f"🎉 **[기준 80% 만족 (합격)]** 최종 가중 충진율: **{final_ratio:.2f}%**")
            else:
                st.error(f"🚨 **[기준 80% 미달 (불합격)]** 최종 가중 충진율: **{final_ratio:.2f}%**")

            now = datetime.now()
            new_record = {
                "사진 이름": uploaded_file.name,
                "날짜시간": now.strftime("%Y-%m-%d %H:%M:%S"),
                "최종 충진율": f"{final_ratio:.2f}%"
            }
            
            if not st.session_state.history or st.session_state.history[0].get("날짜시간") != new_record["날짜시간"]:
                st.session_state.history.insert(0, new_record)

        else:
            with col2:
                st.markdown("##### 2. 정면 보정")
                st.info("4곳 터치 후 분석 버튼 클릭")
            with col3:
                st.markdown("##### 3. 진단 마스크")
                st.info("분석 대기 중")

        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("📋 **분석 이력 기록 열기 / 닫기**", expanded=False):
            if st.session_state.history:
                df = pd.DataFrame(st.session_state.history)
                st.dataframe(df, use_container_width=True)
                
                col_exp1, col_exp2 = st.columns([1, 1])
                with col_exp1:
                    csv_data = df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("💾 CSV 다운로드", data=csv_data, file_name="tile_history.csv", mime="text/csv", use_container_width=True)
                with col_exp2:
                    if st.button("🧹 이력 초기화", use_container_width=True):
                        st.session_state.history = []
                        st.session_state.pts = []
                        st.session_state.coord_key += 1
                        st.rerun()
            else:
                st.caption("저장된 이력이 없습니다.")

else:
    st.session_state.pts = []
    st.info("👈 사이드바에서 열화상 사진을 업로드하세요.")
