FROM python:3.13-trixie

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# run the container as a non-root user
ARG UID=1000
ARG GID=1000

# Create a non-root user
RUN groupadd -g $GID transcode_tycoon && \
    useradd -u $UID -m -g transcode_tycoon transcode_tycoon

USER transcode_tycoon
ENV PATH="/home/transcode_tycoon/.local/bin:${PATH}"
WORKDIR /home/transcode_tycoon

# Copy over project files
COPY --chown=transcode_tycoon:transcode_tycoon ./pyproject.toml ./
COPY --chown=transcode_tycoon:transcode_tycoon ./transcode_tycoon ./transcode_tycoon
RUN mkdir ./logs && chown -R transcode_tycoon:transcode_tycoon /home/transcode_tycoon/logs

# install depdendencies
RUN pip3 install --user uv && uv sync

# make sure we're not running as root
HEALTHCHECK --interval=30s --timeout=3s \
    CMD [ "$(id -u)" -ne 0 ] || exit 1

CMD uv run -m transcode_tycoon
