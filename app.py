import streamlit as st
from google import genai
from google.genai import types
import os
import re
from PIL import Image
from pypdf import PdfReader

st.set_page_config(page_title="Trợ lý Học tập - Thầy Long Bình", page_icon="🤖")
st.title("🤖 Trợ Lý Học Tập - Thầy Long Bình")

st.sidebar.header("🔑 Cấu hình danh sách API Key")
st.sidebar.write("Thầy dán danh sách Key vào đây (mỗi dòng 1 Key). Hệ thống sẽ tự động xoay vòng để tránh quá tải:")

# Khung nhập Key trống để đảm bảo an toàn, không lưu đè Key lên GitHub
keys_input = st.sidebar.text_area("Danh sách API Keys của thầy:", height=120, type="password", placeholder="Dán các mã Key của thầy vào đây, mỗi mã một dòng...")

# Tách danh sách các Key sạch sẽ
api_keys_list = [k.strip() for k in keys_input.split("\n") if k.strip()]

# Thiết lập chỉ số Key đang sử dụng trong Session State
if "key_index" not in st.session_state:
    st.session_state.key_index = 0

# --- HÀM KHỞI TẠO CLIENT TỰ ĐỘNG XOAY VÒNG KEY KHI LỖI QUÁ TẢI ---
def get_gemini_client():
    if not api_keys_list:
        return None
    idx = st.session_state.key_index % len(api_keys_list)
    current_key = api_keys_list[idx]
    try:
        return genai.Client(api_key=current_key)
    except Exception:
        return None

# --- HÀM TỰ ĐỘNG ĐỔI SANG KEY TIẾP THEO ---
def rotate_api_key():
    if len(api_keys_list) > 1:
        st.session_state.key_index = (st.session_state.key_index + 1) % len(api_keys_list)
        return True
    return False

# Kiểm tra trạng thái kích hoạt hệ thống
api_ready = len(api_keys_list) > 0

if not api_ready:
    st.sidebar.warning("Vui lòng nhập danh sách mã API Key để kích hoạt ứng dụng.")
    st.info("👈 Thầy ơi, hãy dán 3 mã API Key của thầy (mỗi dòng một mã) vào ô trống bên góc trái này để bắt đầu nhé!")

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

# --- 4. HÀM TÌM ĐƯỜNG DẪN ẢNH ĐÁP ÁN ---
def find_image_path(lesson_cleaned):
    if not os.path.exists("images"):
        return None
    for file_name in os.listdir("images"):
        name_without_ext, ext = os.path.splitext(file_name)
        if clean_text(name_without_ext) == lesson_cleaned:
            return os.path.join("images", file_name)
    return None

# --- 5. KHỞI TẠO TRẠNG THÁI HỆ THỐNG ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_step" not in st.session_state:
    st.session_state.current_step = "CHAO_HOI"
if "selected_lesson" not in st.session_state:
    st.session_state.selected_lesson = None
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None

SYSTEM_PROMPT = (
    "Bạn là trợ lý học tập môn Toán và Khoa học tự nhiên của thầy Long Bình tại trường THCS Hoàng Văn Thụ. "
    "Nhiệm vụ của bạn là đóng vai một giáo viên sư phạm chuẩn mực. Dựa vào nội dung tài liệu PDF được cung cấp, "
    "hãy tìm câu hỏi bài tập mà học sinh đang yêu cầu để hướng dẫn học sinh giải theo từng bước nhỏ.\n"
    "TỪNG BƯỚC MỘT: Chỉ gợi ý hoặc đặt câu hỏi mở cho bước đầu tiên, chờ học sinh trả lời rồi mới nhận xét và hướng dẫn tiếp.\n"
    "TUYỆT ĐỐI KHÔNG ĐƯỢC giải hết toàn bộ bài, không đưa thẳng đáp án chữ ngay từ đầu ở tiến trình này."
)

MODEL_NAME = "gemini-2.5-flash"
pdf_content = extract_text_from_pdf("Test.pdf")

# --- GIAO DIỆN ỨNG DỤNG CHÍNH ---
if api_ready:
    client = get_gemini_client()
    
    if st.session_state.current_step == "CHAO_HOI":
        welcome_text = "Chào em, thầy là trợ lý của thầy Long Bình. Hôm nay em cần thầy hỗ trợ bài tập nào? (Ví dụ nhập: Bài 1, Bài 2,...)"
        st.session_state.messages = [{"role": "assistant", "content": welcome_text}]
        st.session_state.current_step = "CHO_HOC_SINH_CHON_BAI"
        st.session_state.chat_session = None

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if st.session_state.current_step == "CHO_HOC_SINH_CHON_BAI":
        if user_input := st.chat_input("Nhập tên bài tập tại đây..."):
            st.session_state.selected_lesson = user_input
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.current_step = "CHO_HOC_SINH_CHON_HUONG_GIAI"
            st.rerun()

    elif st.session_state.current_step == "CHO_HOC_SINH_CHON_HUONG_GIAI":
        st.warning(f"Thầy đang xử lý yêu cầu cho: **{st.session_state.selected_lesson}**")
        st.write("Em muốn thầy hỗ trợ theo hướng nào dưới đây?")
        
        col1, col2 = st.columns(2)
        cleaned_lesson = clean_text(st.session_state.selected_lesson)
        
        with col1:
            if st.button("📖 Gợi ý từng bước"):
                st.session_state.messages.append({"role": "user", "content": "Gợi ý từng bước"})
                st.session_state.current_step = "KICH_HOAT_GOI_Y_DAU_TIEN"
                st.rerun()
                
        with col2:
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

    # --- LUỒNG LUÂN PHIÊN KEY ---
    elif st.session_state.current_step == "KICH_HOAT_GOI_Y_DAU_TIEN":
        with st.spinner("Thầy đang đọc tài liệu PDF để chuẩn bị câu hỏi gợi ý..."):
            lesson_org = st.session_state.selected_lesson
            context_prompt = (
                f"{SYSTEM_PROMPT}\n"
                f"NỘI DUNG TÀI LIỆU TOÀN BỘ BÀI TẬP (PDF):\n{pdf_content}\n\n"
                f"YÊU CẦU HIỆN TẠI: Học sinh chọn bài: '{lesson_org}'. "
                f"Hãy tìm bài này trong PDF và đưa ra câu hỏi gợi mở bước đầu tiên."
            )

            for _ in range(len(api_keys_list)):
                client = get_gemini_client()
                try:
                    st.session_state.chat_session = client.chats.create(
                        model=MODEL_NAME,
                        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
                    )
                    response = st.session_state.chat_session.send_message(context_prompt)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    st.session_state.current_step = "DANG_GOI_Y"
                    st.rerun()
                except Exception as e:
                    if "429" in str(e) and rotate_api_key():
                        continue  
                    else:
                        st.error(f"Hệ thống bận (Lỗi: {e}). Thầy/em chờ vài giây rồi gõ lại nhé!")
                        break

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
                for _ in range(len(api_keys_list)):
                    try:
                        response = st.session_state.chat_session.send_message(user_input)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                        st.rerun()
                    except Exception as e:
                        if "429" in str(e) and rotate_api_key():
                            client = get_gemini_client()
                            try:
                                st.session_state.chat_session = client.chats.create(
                                    model=MODEL_NAME,
                                    config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
                                )
                                full_context = f"Tài liệu PDF ngữ cảnh:\n{pdf_content}\n\nHọc sinh đang trao đổi tiếp câu hỏi bài tập. Đây là câu trả lời mới nhất của học sinh: {user_input}"
                                response = st.session_state.chat_session.send_message(full_context)
                                st.session_state.messages.append({"role": "assistant", "content": response.text})
                                rerun()
                            except Exception:
                                continue
                        else:
                            st.warning("🤖 AI đang xử lý dồn ứ tin nhắn. Em hãy chờ 5 giây rồi gõ lại câu trả lời nhé!")
