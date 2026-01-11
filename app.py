import streamlit as st
import fitz  # PyMuPDF
import re
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter
import io

# --- PDF 전처리 클래스 ---
class PDFChatbotPreprocessor:
    def __init__(self, chunk_size=600, chunk_overlap=100):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )

    def extract_text_from_pdf(self, pdf_file):
        # 업로드된 파일 객체에서 직접 읽기
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
            "total_chunks": len(chunks),
            "content": [{"id": f"{pdf_file.name}_{i}", "text": chunk} for i, chunk in enumerate(chunks)]
        }

# --- 웹 화면 구성 ---
st.set_page_config(page_title="대량 PDF 전처리 마스터", page_icon="📚", layout="wide")

st.title("📚 대량 PDF 업무 자동화 도구")
st.write("주인님, 이제 여러 파일을 한꺼번에 드래그하거나 선택하여 처리하실 수 있습니다.")

# 설정 옵션 (사이드바)
st.sidebar.header("⚙️ 설정")
chunk_size = st.sidebar.slider("글자 자르기 단위", 100, 2000, 600)
chunk_overlap = st.sidebar.slider("중복 허용 범위", 0, 500, 100)

# 핵심 업데이트: accept_multiple_files=True (드래그 앤 드롭 및 다중 선택 가능)
uploaded_files = st.file_uploader(
    "PDF 파일들을 여기에 드래그하거나 클릭하여 업로드하세요 (최대 100개 이상 가능)", 
    type="pdf", 
    accept_multiple_files=True
)

if uploaded_files:
    st.info(f"현재 {len(uploaded_files)}개의 파일이 대기 중입니다.")
    
    if st.button("🚀 모든 파일 전처리 및 통합 시작"):
        all_processed_data = []
        progress_bar = st.progress(0)
        
        preprocessor = PDFChatbotPreprocessor(chunk_size, chunk_overlap)
        
        for i, file in enumerate(uploaded_files):
            # 파일당 처리 실행
            result = preprocessor.process(file)
            all_processed_data.append(result)
            
            # 진행률 표시
            progress_bar.progress((i + 1) / len(uploaded_files))
            
        st.success(f"✅ 총 {len(uploaded_files)}개의 파일 전처리가 완료되었습니다!")

        # 1. 통합 JSON 파일 생성
        final_json = json.dumps(all_processed_data, ensure_ascii=False, indent=4)
        
        # 2. 결과 다운로드 및 미리보기
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="📥 통합 JSON 결과 다운로드",
                data=final_json,
                file_name="bulk_processed_data.json",
                mime="application/json"
            )
        
        with col2:
            # (옵션) 구글 시트 기능이 활성화되어 있다면 여기서 한 번에 전송 가능
            st.write("팁: 다운로드 버튼을 눌러 결과물을 확인하세요.")

        # 미리보기 (최대 3개 파일만 샘플로 표시)
        with st.expander("결과 데이터 샘플 보기 (상위 3개)"):
            st.json(all_processed_data[:3])

else:
    st.write("주인님, 파일을 기다리고 있습니다. 폴더에서 파일을 잡아서 이 창으로 끌어다 놓으시면 됩니다.")
