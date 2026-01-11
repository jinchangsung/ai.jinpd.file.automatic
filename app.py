import streamlit as st
import fitz
import re
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- PDF 전처리 클래스 ---
class PDFChatbotPreprocessor:
    def __init__(self, chunk_size=600, chunk_overlap=100):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )

    def extract_text_from_pdf(self, pdf_file):
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        return full_text

    def clean_text(self, text):
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'-\s*\d+\s*-', '', text)
        return text.strip()

    def process(self, pdf_file):
        raw_text = self.extract_text_from_pdf(pdf_file)
        cleaned_text = self.clean_text(raw_text)
        chunks = self.text_splitter.split_text(cleaned_text)
        
        return {
            "file_name": pdf_file.name,
            "char_count": len(cleaned_text), # 이 파일에서 추출된 글자 수
            "total_chunks": len(chunks),
            "content": [{"id": f"{pdf_file.name}_{i}", "text": chunk} for i, chunk in enumerate(chunks)]
        }

# --- 웹 화면 구성 ---
st.set_page_config(page_title="대량 PDF 전처리 마스터", page_icon="📚", layout="wide")
st.title("📚 대량 PDF 업무 자동화 도구")

uploaded_files = st.file_uploader(
    "PDF 파일들을 드래그하거나 선택하세요", 
    type="pdf", 
    accept_multiple_files=True
)

if uploaded_files:
    st.info(f"현재 {len(uploaded_files)}개의 파일이 대기 중입니다.")
    
    if st.button("🚀 전처리 및 글자 수 합산 시작"):
        all_processed_data = []
        total_characters = 0 # 총 글자 수를 저장할 변수 초기화
        
        status_message = st.empty()
        progress_bar = st.progress(0)
        
        preprocessor = PDFChatbotPreprocessor()
        
        for i, file in enumerate(uploaded_files):
            current_num = i + 1
            status_message.info(f"⏳ {current_num}번째 파일 처리 중: **{file.name}**")
            
            # 실제 처리 실행
            result = preprocessor.process(file)
            all_processed_data.append(result)
            
            # 글자 수 누적
            total_characters += result["char_count"]
            
            # 진행률 업데이트
            progress_bar.progress(current_num / len(uploaded_files))
            st.toast(f"{file.name} 완료! (+{result['char_count']:,}자)", icon="📝")

        # --- 결과 대시보드 표시 ---
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("총 처리 파일", f"{len(uploaded_files)}개")
        with col2:
            st.metric("총 추출 글자 수", f"{total_characters:,}자")
        with col3:
            avg_chars = total_characters // len(uploaded_files) if uploaded_files else 0
            st.metric("파일당 평균 글자 수", f"{avg_chars:,}자")

        status_message.success(f"✨ 모든 처리가 완료되었습니다! (총 {total_characters:,}자 추출)")

        # 통합 JSON 다운로드
        final_json = json.dumps(all_processed_data, ensure_ascii=False, indent=4)
        st.download_button(
            label="📥 통합 JSON 결과 다운로드",
            data=final_json,
            file_name="bulk_processed_data.json",
            mime="application/json"
        )
