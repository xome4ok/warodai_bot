FROM alpine:3.5

RUN apk add --no-cache python3 && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    rm -r /root/.cache

RUN pip3 install -r requirements.txt

ENV TOKEN

EXPOSE 80

ENTRYPOINT ["python3", "bot.py", $TOKEN]