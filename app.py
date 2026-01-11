import streamlit as st
import fitz  # PyMuPDF
import re
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- 1. PDF 전처리 핵심 클래스 (청크 설정 복구) ---
class PDFChatbotPreprocessor:
    def __init__(self, chunk_size, chunk_overlap):
        # 주인님, 여기서 청크 크기와 겹침 정도를 설정합니다.
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

    def extract_text_from_pdf(self, pdf_file):
        """PDF에서 원문 텍스트 추출"""
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        return full_text

    def clean_text(self, text):
        """불필요한 공백 및 페이지 번호 제거"""
        text = re.sub(r'\s+', ' ', text) # 연속 공백 제거
        text = re.sub(r'-\s*\d+\s*-', '', text) # 페이지 번호 제거
        return text.strip()

    def process(self, pdf_file):
        """추출 -> 정제 -> 청크 분할 과정을 한 번에 수행"""
        raw_text = self.extract_text_from_pdf(pdf_file)
        cleaned_text = self.clean_text(raw_text)
        
        # 텍스트를 청크 단위로 분할
        chunks = self.text_splitter.split_text(cleaned_text)
        
        return {
            "file_name": pdf_file.name,
            "char_count": len(cleaned_text),
            "total_chunks": len(chunks),
            "content": [{"id": f"{pdf_file.name}_{i}", "text": chunk} for i, chunk in enumerate(chunks)]
        }

# --- 2. 웹 화면 구성 (레이아웃 및 설정) ---
st.set_page_config(page_title="통합 PDF 전처리 마스터", page_icon="🚀", layout="wide")

st.title("🚀 통합 PDF 업무 자동화 시스템")
st.write("주인님, 청크 설정 기능을 복구하고 모든 최신 기능을 통합했습니다.")

# --- 3. 사이드바 설정 (복구된 부분) ---
st.sidebar.header("⚙️ 전처리 상세 설정")
chunk_size = st.sidebar.slider("청크 크기 (Chunk Size)", 100, 2000, 600, help="한 번에 자를 글자 수입니다.")
chunk_overlap = st.sidebar.slider("청크 중복 (Chunk Overlap)", 0, 500, 100, help="문맥 연결을 위해 겹칠 글자 수입니다.")

# --- 4. 파일 업로드 (다중 선택 & 드래그 앤 드롭) ---
uploaded_files = st.file_uploader(
    "PDF 파일들을 여기에 드래그하거나 클릭하여 업로드하세요", 
    type="pdf", 
    accept_multiple_files=True
)

if uploaded_files:
    st.info(f"현재 **{len(uploaded_files)}개**의 파일이 대기 중입니다.")
    
    if st.button("🏁 모든 파일 일괄 처리 시작"):
        all_processed_data = []
        total_characters = 0
        
        # 메시지 표시 공간과 진행바
        status_message = st.empty()
        progress_bar = st.progress(0)
        
        # 복구된 설정값을 클래스에 전달
        preprocessor = PDFChatbotPreprocessor(chunk_size, chunk_overlap)
        
        for i, file in enumerate(uploaded_files):
            current_num = i + 1
            # 실시간 상태 업데이트
            status_message.info(f"⏳ {current_num}번째 파일 처리 중: **{file.name}**")
            st.toast(f"{current_num}번째 분석 중...", icon="🔍")
            
            # 파일 처리
            result = preprocessor.process(file)
            all_processed_data.append(result)
            
            # 글자 수 누적 합산
            total_characters += result["char_count"]
            
            # 진행바 업데이트
            progress_bar.progress(current_num / len(uploaded_files))

        # --- 5. 결과 대시보드 표시 ---
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("총 처리 파일", f"{len(uploaded_files)}개")
        with col2:
            st.metric("총 추출 글자 수", f"{total_characters:,}자")
        with col3:
            avg_chunks = sum(item["total_chunks"] for item in all_processed_data) // len(uploaded_files)
            st.metric("파일당 평균 청크 수", f"{avg_chunks}개")

        status_message.success(f"✨ 모든 작업이 완료되었습니다! (총 {total_characters:,}자 추출)")
        st.toast("모든 파일 전처리 완료!", icon="🎉")

        # 통합 JSON 다운로드 버튼
        final_json = json.dumps(all_processed_data, ensure_ascii=False, indent=4)
        st.download_button(
            label="📥 통합 JSON 결과 다운로드",
            data=final_json,
            file_name="integrated_chatbot_data.json",
            mime="application/json"
        )
        
        # 데이터 구조 샘플 확인
        with st.expander("데이터 샘플 미리보기"):
            st.json(all_processed_data[:2]) # 상위 2개 파일만 표시
