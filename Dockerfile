FROM astral/uv:python3.12-trixie-slim

# docker image build params
ARG H_GID=1050
ARG H_UID=1050

# uv disable development dependencies
ENV UV_NO_DEV=1

# timezone
RUN DEBIAN_FRONTEND=noninteractive TZ=Europe/Berlin apt-get install -y tzdata \
	&& cp /usr/share/zoneinfo/Europe/Berlin /etc/localtime \
	&& echo "Europe/Berlin" > /etc/timezone 

# system and user setup 
RUN addgroup --gid $H_GID user \
	&& adduser user --uid $H_UID --ingroup user --gecos "" --home /home/user/ --disabled-password \
	&& mkdir /home/user/src/ \
	&& chown -R user:user /home/user/

# run in user's home
USER user

# py install: setup venv and install dependencies
COPY --chown=user:user ./requirements-frozen.txt /home/user/requirements-frozen.txt
RUN uv venv /home/user/.venv 
ENV PATH="/home/user/.venv/bin:$PATH"
RUN uv pip install -r /home/user/requirements-frozen.txt

# copy source code
COPY --chown=user:user ./server/ /home/user/server/

# run
WORKDIR /home/user/server/
CMD ["uv", "run", "uvicorn", "core.web.main:app", "--host", "0.0.0.0", "--port", "8000"]