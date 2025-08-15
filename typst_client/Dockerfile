FROM archlinux
COPY . .
RUN pacman --noconfirm -Syu && \
  pacman --noconfirm -S typst iproute2 python3 nginx
RUN python3 -m venv /venv && \
  . /venv/bin/activate && \
  pip install -r /src/requirements.txt && \
  deactivate
RUN mv nginx.conf /etc/nginx/nginx.conf && \
	mv *.html /usr/share/nginx/html/

CMD nginx & . /venv/bin/activate && python3 /src/run.py
