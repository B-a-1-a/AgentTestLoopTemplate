FROM python:3.11-slim

RUN useradd -m -u 10001 sandbox
WORKDIR /sandbox

COPY entrypoint.sh /sandbox/entrypoint.sh
RUN chmod +x /sandbox/entrypoint.sh

USER sandbox
ENTRYPOINT ["/sandbox/entrypoint.sh"]
