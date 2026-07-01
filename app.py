import streamlit as st
import google.generativeai as genai
import os
import re
from PIL import Image
from pypdf import PdfReader

st.set_page_config(page_title="Trợ lý Học tập - Thầy Long Bình", page_icon="🤖")
st.title("🤖 Trợ Lý Học Tập - Thầy Long Bình")

# --- 1. CẤU HÌNH API KEY TẠI SIDEBAR ---
st.sidebar.header("🔑 Cấu hình hệ thống")
api_key_input = st.sidebar.text_input("Nhập API Key của thầy:", type="password")

api_ready = False
if api_key_input:
    try:
        genai.configure(api_key=api_key_input)
        # Sử dụng gemini-1.5-flash để tối ưu tốc độ phản hồi
        model = genai.GenerativeModel("gemini-1.5-flash")
        api_ready = True
    except Exception as e:
        st.sidebar.error(f"Lỗi cấu hình API Key: {e}")
else:
    st.sidebar.warning("Vui lòng nhập mã API Key ở đây để kích hoạt ứng dụng.")
    st.info("👈 Thầy ơi, hãy nhập hoặc dán mã API Key vào ô bên góc trái để ứng dụng hoạt động nhé!")

# --- 2. HÀM CHUẨN HÓA TIẾNG VIỆT KHÔNG DẤU ---
def clean_text(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', text)
    text = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', text)
    text = re.sub(r'[ìíịỉĩ]', 'i', text)
    text = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', text)
    text = re.sub(r'[ùúụủũưừứựửữ]', 'u', text)
    text = re.sub(r'[ỳýỵỷỹ]', 'y', text)
    text = re.sub(r'[đ]', 'd', text)
    text = re.sub(r'[\s\W_]', '', text)
    return text

# --- 3. HÀM ĐỌC VĂN BẢN TỪ FILE Test.pdf ---
def extract_text_from_pdf(pdf_path="Test.pdf"):
    if not os.path.exists(pdf_path):
        return ""
    try:
        reader = PdfReader(pdf_path)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    except Exception:
        return ""

# --- 4. HÀM TÌM ĐƯỜNG DẪN ẢNH ĐÁP ÁN TRONG THƯ MỤC IMAGES ---
def find_image_path(lesson_cleaned):
    if not os.path.exists("images"):
        return None
    for file_name in os.listdir("images"):
        name_without_ext, ext = os.path.splitext(file_name)
        if clean_text(name_without_ext) == lesson_cleaned:
            return os.path.join("images", file_name)
    return None

# --- 5. KHỞI TẠO TRẠNG THÁI HỆ THỐNG (SESSION STATE) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_step" not in st.session_state:
    st.session_state.current_step = "CHAO_HOI"
if "selected_lesson" not in st.session_state:
    st.session_state.selected_lesson = None

SYSTEM_PROMPT = (
    "Bạn là trợ lý học tập môn Toán và Khoa học tự nhiên của thầy Long Bình tại trường THCS Hoàng Văn Thụ. "
    "Nhiệm vụ của bạn là đóng vai một giáo viên sư phạm chuẩn mực. Dựa vào nội dung tài liệu PDF được cung cấp, "
    "hãy tìm câu hỏi bài tập mà học sinh đang yêu cầu để hướng dẫn học sinh giải theo từng bước nhỏ.\n"
    "TỪNG BƯỚC MỘT: Chỉ gợi ý hoặc đặt câu hỏi mở cho bước đầu tiên, chờ học sinh trả lời rồi mới nhận xét và hướng dẫn tiếp.\n"
    "TUYỆT ĐỐI KHÔNG ĐƯỢC giải hết toàn bộ bài, không đưa thẳng đáp án chữ ngay từ đầu ở tiến trình này."
)

# Đọc sẵn nội dung PDF làm ngữ cảnh cho AI gợi ý
pdf_content = extract_text_from_pdf("Test.pdf")

# --- CHỈ CHẠY GIAO DIỆN CHAT KHI ĐÃ ĐIỀN API KEY ---
if api_ready:
    # --- BƯỚC 1: CHÀO HỎI TỰ ĐỘNG ---
    if st.session_state.current_step == "CHAO_HOI":
        welcome_text = "Chào em, thầy là trợ lý của thầy Long Bình. Hôm nay em cần thầy hỗ trợ bài tập nào? (Ví dụ nhập: Bài 1, Bài 2,...)"
        st.session_state.messages = [{"role": "assistant", "content": welcome_text}]
        st.session_state.current_step = "CHO_HOC_SINH_CHON_BAI"

    # Hiển thị lịch sử trò chuyện trực quan
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # --- BƯỚC 2: NHẬN TÊN BÀI TẬP TỪ HỌC SINH ---
    if st.session_state.current_step == "CHO_HOC_SINH_CHON_BAI":
        if user_input := st.chat_input("Nhập tên bài tập tại đây..."):
            st.session_state.selected_lesson = user_input
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.current_step = "CHO_HOC_SINH_CHON_HUONG_GIAI"
            st.rerun()

    # --- BƯỚC 3: PHÂN NHÁNH QUYẾT ĐỊNH ---
    elif st.session_state.current_step == "CHO_HOC_SINH_CHON_HUONG_GIAI":
        st.warning(f"Thầy đang xử lý yêu cầu cho: **{st.session_state.selected_lesson}**")
        st.write("Em muốn thầy hỗ trợ theo hướng nào dưới đây?")
        
        col1, col2 = st.columns(2)
        cleaned_lesson = clean_text(st.session_state.selected_lesson)
        
        with col1:
            # LUỒNG 1: AI đọc PDF và đưa ra gợi ý sư phạm từng bước nhỏ
            if st.button("📖 Gợi ý từng bước"):
                st.session_state.messages.append({"role": "user", "content": "Gợi ý từng bước"})
                st.session_state.current_step = "KICH_HOAT_GOI_Y_DAU_TIEN"
                st.rerun()
                
        with col2:
            # LUỒNG 2: Xuất trực tiếp file ảnh đáp án từ folder images
            if st.button("🎯 Xem đáp án cụ thể"):
                st.session_state.messages.append({"role": "user", "content": "Xem đáp án cụ thể"})
                
                img_path = find_image_path(cleaned_lesson)
                if img_path:
                    with st.chat_message("assistant"):
                        st.image(Image.open(img_path), caption=f"Đáp án hình ảnh chính xác cho {st.session_state.selected_lesson}")
                    st.session_state.messages.append({"role": "assistant", "content": f"[Đã hiển thị ảnh đáp án cho {st.session_state.selected_lesson}]"})
                else:
                    err_msg = f"Thầy chưa tìm thấy ảnh đáp án cho '{st.session_state.selected_lesson}' trong folder 'images'."
                    with st.chat_message("assistant"):
                        st.error(err_msg)
                    st.session_state.messages.append({"role": "assistant", "content": err_msg})
                
                st.session_state.current_step = "CHAO_HOI"
                st.session_state.selected_lesson = None
                st.button("Hỏi bài tập khác 🔄")

    # --- LUỒNG GỢI Ý: KÍCH HOẠT AI ĐỌC PDF ĐỂ GỢI Ý CÂU ĐẦU TIÊN ---
    elif st.session_state.current_step == "KICH_HOAT_GOI_Y_DAU_TIEN":
        # SỬA LỖI CHỮ VIẾT HOA TẠI ĐÂY (Thay St.spinner bằng st.spinner)
        with st.spinner("Thầy đang đọc tài liệu PDF để chuẩn bị câu hỏi gợi ý..."):
            lesson_org = st.session_state.selected_lesson
            
            if pdf_content:
                context_prompt = (
                    f"{SYSTEM_PROMPT}\n"
                    f"NỘI DUNG TÀI LIỆU TOÀN BỘ BÀI TẬP (PDF):\n{pdf_content}\n\n"
                    f"YÊU CẦU: Học sinh đang cần hướng dẫn giải bài: '{lesson_org}'.\n"
                    f"Hãy đối chiếu bài toán này trong tài liệu PDF để tìm câu hỏi, từ đó đưa ra câu hỏi gợi mở bước đầu tiên cho học sinh."
                )
            else:
                context_prompt = (
                    f"{SYSTEM_PROMPT}\n"
                    f"Học sinh đang yêu cầu làm bài: {lesson_org} (Không tìm thấy file Test.pdf).\n"
                    f"Hãy tự đưa ra câu hỏi gợi mở bước 1 dựa theo kiến thức toán học phổ thông cho bài này."
                )

            try:
                response = model.generate_content(context_prompt).text
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.current_step = "DANG_GOI_Y"
                st.rerun()
            except Exception as e:
                # In chi tiết lỗi kỹ thuật để thầy dễ dàng chẩn đoán kiểm tra API Key
                st.error(f"Lỗi kết nối với Gemini AI: {e}")
                st.info("💡 Mẹo: Thầy kiểm tra lại mã API Key ở sidebar hoặc hạn mức tài khoản xem sao nhé!")

    # --- LUỒNG GỢI Ý: TIẾP TỤC DẪN DẮT HỌC SINH GIẢI BÀI ---
    elif st.session_state.current_step == "DANG_GOI_Y":
        if user_input := st.chat_input("Nhập câu trả lời hoặc thắc mắc của em..."):
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            if "xong" in user_input.lower() or "hoàn thành" in user_input.lower():
                feedback = "Tuyệt vời! Em làm tốt lắm. Hãy chuẩn bị sang bài tập tiếp theo nhé!"
                st.session_state.messages.append({"role": "assistant", "content": feedback})
                st.session_state.current_step = "CHAO_HOI"
                st.session_state.selected_lesson = None
                st.rerun()
            else:
                lesson_org = st.session_state.selected_lesson
                
                context_prompt = (
                    f"{SYSTEM_PROMPT}\n"
                    f"NỘI DUNG TÀI LIỆU TOÀN BỘ BÀI TẬP (PDF):\n{pdf_content}\n\n"
                    f"Ngữ cảnh: Học sinh đang giải bài: '{lesson_org}'.\n"
                    f"Học sinh phản hồi: {user_input}.\n"
                    f"Nhiệm vụ: Dựa vào nội dung bài tập trong tài liệu PDF, nhận xét câu trả lời của học sinh và đưa ra câu hỏi gợi mở bước tiếp theo."
                )
                        
                try:
                    response = model.generate_content(context_prompt).text
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()
                except Exception as e:
                    st.error(f"Hệ thống gặp gián đoạn nhỏ từ AI: {e}")
