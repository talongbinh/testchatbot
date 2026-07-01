import streamlit as st
import google.generativeai as genai
import os
from PIL import Image
from pypdf import PdfReader

st.title("🤖 Trợ Lý Học Tập - Thầy Long Bình")

# --- 1. ĐƯA Ô NHẬP API KEY QUAY TRỞ LẠI SIDEBAR ---
st.sidebar.header("🔑 Cấu hình hệ thống")
api_key_input = st.sidebar.text_input("Nhập API Key của thầy:", type="password")

# Kiểm tra và kích hoạt API Key trực tiếp từ sidebar
api_ready = False
if api_key_input:
    try:
        genai.configure(api_key=api_key_input)
        model = genai.GenerativeModel("gemini-1.5-flash")
        api_ready = True
    except Exception:
        st.sidebar.error("Mã API Key không hợp lệ. Thầy kiểm tra lại nhé!")
else:
    st.sidebar.warning("Vui lòng nhập mã API Key ở đây để kích hoạt ứng dụng.")
    st.info("👈 Thầy ơi, hãy nhập hoặc dán mã API Key vào ô bên góc trái để ứng dụng hoạt động nhé!")

# --- 2. KHỞI TẠO TRẠNG THÁI CUỘC HỘI THOẠI (SESSION STATE) ---
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
    "TUYỆT ĐỐI KHÔNG ĐƯỢC giải hết toàn bộ bài, không đưa thẳng đáp án chữ ngay từ đầu."
)

# Hàm đọc văn bản từ file Test.pdf
def extract_text_from_pdf(pdf_path="Test.pdf"):
    if not os.path.exists(pdf_path):
        return None
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception:
        return None

# Hàm tìm đường dẫn ảnh đáp án trong thư mục images
def find_image_path(lesson):
    possible_files = [
        f"images/{lesson}.jpg", f"images/{lesson}.png", 
        f"images/{lesson}.jpeg", f"images/{lesson}.JPG", f"images/{lesson}.PNG"
    ]
    for f_path in possible_files:
        if os.path.exists(f_path):
            return f_path
    return None

# --- CHỈ HIỂN THỊ VÀ CHẠY GIAO DIỆN CHAT KHI ĐÃ ĐIỀN API KEY ---
if api_ready:
    # --- BƯỚC 1: CHÀO HỎI TỰ ĐỘNG ---
    if st.session_state.current_step == "CHAO_HOI":
        welcome_text = "Chào em, thầy là trợ lý của thầy Long Bình. Hôm nay em cần thầy hỗ trợ bài tập nào? (Ví dụ nhập: bài 1, bài 2,...)"
        st.session_state.messages = [{"role": "assistant", "content": welcome_text}]
        st.session_state.current_step = "CHO_HOC_SINH_CHON_BAI"

    # Hiển thị lịch sử trò chuyện
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # --- BƯỚC 2: NHẬN TÊN BÀI TẬP TỪ HỌC SINH ---
    if st.session_state.current_step == "CHO_HOC_SINH_CHON_BAI":
        if user_input := st.chat_input("Nhập tên bài tập tại đây..."):
            st.session_state.selected_lesson = user_input.lower().replace(" ", "")
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.current_step = "CHO_HOC_SINH_CHON_HUONG_GIAI"
            st.rerun()

    # --- BƯỚC 3: HIỂN THỊ LỰA CHỌN NÚT BẤM ---
    elif st.session_state.current_step == "CHO_HOC_SINH_CHON_HUONG_GIAI":
        st.warning(f"Thầy đang xử lý yêu cầu cho bài: **{st.session_state.selected_lesson.upper()}**")
        st.write("Em muốn thầy hỗ trợ theo hướng nào dưới đây?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📖 Gợi ý từng bước"):
                st.session_state.messages.append({"role": "user", "content": "Gợi ý từng bước"})
                st.session_state.current_step = "KICH_HOAT_GOI_Y_DAU_TIEN"
                st.rerun()
                
        with col2:
            if st.button("🎯 Xem đáp án cụ thể"):
                st.session_state.messages.append({"role": "user", "content": "Xem đáp án cụ thể"})
                
                img_path = find_image_path(st.session_state.selected_lesson)
                if img_path:
                    with st.chat_message("assistant"):
                        st.image(Image.open(img_path), caption=f"Đáp án chính xác cho bài {st.session_state.selected_lesson.upper()}")
                    st.session_state.messages.append({"role": "assistant", "content": f"[Đã hiển thị ảnh đáp án bài {st.session_state.selected_lesson}]"})
                else:
                    err_msg = f"Thầy chưa tìm thấy file ảnh '{st.session_state.selected_lesson}.jpg' trong thư mục 'images'."
                    with st.chat_message("assistant"):
                        st.error(err_msg)
                    st.session_state.messages.append({"role": "assistant", "content": err_msg})
                
                st.session_state.current_step = "CHAO_HOI"
                st.session_state.selected_lesson = None
                st.button("Hỏi bài tập khác 🔄")

    # --- BƯỚC EXTRA: ĐỌC TÀI LIỆU PDF VÀ KÍCH HOẠT CÂU GỢI Ý ĐẦU TIÊN ---
    elif st.session_state.current_step == "KICH_HOAT_GOI_Y_DAU_TIEN":
        with st.spinner("Thầy đang lục tìm đề bài trong file Test.pdf để chuẩn bị gợi ý..."):
            lesson_key = st.session_state.selected_lesson
            pdf_content = extract_text_from_pdf("Test.pdf")
            
            if pdf_content:
                context_prompt = (
                    f"{SYSTEM_PROMPT}\n"
                    f"NỘI DUNG TÀI LIỆU TOÀN BỘ BÀI TẬP (PDF):\n{pdf_content}\n\n"
                    f"YÊU CẦU: Học sinh đang cần hướng dẫn giải bài: {lesson_key.upper()}.\n"
                    f"Hãy lục tìm nội dung bài này trong tài liệu trên, sau đó đưa ra câu chào và gợi ý/bước hỏi đầu tiên cho học sinh."
                )
            else:
                context_prompt = (
                    f"{SYSTEM_PROMPT}\n"
                    f"Học sinh đang yêu cầu làm bài: {lesson_key.upper()} (Không tìm thấy file Test.pdf trên hệ thống).\n"
                    f"Hãy tự đưa ra câu hỏi gợi mở bước 1 dựa theo kiến thức toán phổ thông cho bài này."
                )

            try:
                response = model.generate_content(context_prompt).text
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.current_step = "DANG_GOI_Y"
                st.rerun()
            except Exception:
                st.error("Gặp gián đoạn khi kết nối với AI. Em vui lòng gõ tin nhắn bất kỳ để thử lại nhé!")
                if user_input := st.chat_input("Gõ chữ bất kỳ để thử lại..."):
                    st.rerun()

    # --- BƯỚC 4: TIẾN TRÌNH THẢO LUẬN, GỢI Ý TIẾP THEO ---
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
                lesson_key = st.session_state.selected_lesson
                pdf_content = extract_text_from_pdf("Test.pdf")
                
                context_prompt = (
                    f"{SYSTEM_PROMPT}\n"
                    f"NỘI DUNG TÀI LIỆU TOÀN BỘ BÀI TẬP (PDF):\n{pdf_content}\n\n"
                    f"Ngữ cảnh: Học sinh đang giải bài: {lesson_key.upper()}.\n"
                    f"Học sinh phản hồi: {user_input}.\n"
                    f"Nhiệm vụ: Nhận xét câu trả lời và đưa ra câu hỏi gợi mở bước tiếp theo dựa trên tài liệu."
                )
                        
                try:
                    response = model.generate_content(context_prompt).text
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()
                except Exception:
                    st.error("Hệ thống gặp gián đoạn nhỏ, em thử gõ lại câu trả lời nhé!")
