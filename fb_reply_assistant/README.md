# FB Reply Assistant

Tool Python dùng OpenAI API để gợi ý trả lời Messenger Facebook.

Mục tiêu:
- Hỗ trợ trả lời tin nhắn đã nhận.
- Không spam.
- Không tự nhắn người lạ.
- Không tự gửi tin qua Facebook.

## Cài đặt

```bash
cd D:\my_project\fb_reply_assistant
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Tạo file `.env` từ `.env.example`, rồi điền API key:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-5.4-mini
```

## Chạy

```bash
python main.py
```

Nhập:
- tên người nhắn
- nội dung tin nhắn

Tool sẽ sinh 3 câu trả lời:
1. dễ thương
2. lịch sự
3. từ chối khéo

## Ghi chú

Persona nằm trong `persona.txt`, có thể chỉnh trực tiếp để thay đổi phong cách trả lời.
