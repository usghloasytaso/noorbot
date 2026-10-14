FROM python:3.12-slim

# تنظیم متغیرهای محیطی استاندارد
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

# ساخت کاربر غیریشه (مورد نیاز Hugging Face Spaces و امنیت کانتینر)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

COPY --chown=user . .

EXPOSE 7860 8080

CMD ["python", "-m", "bot"]
