#Dockerfile OxChief robot client and base station client.

#Verified on Raspberry Pi 4 / Raspbian - Debian GNU/Linux 11 (bullseye)
ARG base_image=python:3.10.9-slim-bullseye

FROM $base_image
WORKDIR  /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:$PATH \
    RUST_VERSION=1.50.0

RUN apt-get update
    # basic deps
RUN  apt-get install -y -qq git mercurial cloc openssl ssh gettext sudo build-essential
    # voice support
RUN  apt-get install -y -qq libffi-dev libsodium-dev libopus-dev ffmpeg
    # apt is so noisy
    # > /dev/null && \
    # install rust with rustup
RUN apt-get install wget
RUN dpkgArch="$(dpkg --print-architecture)" && \
    case "${dpkgArch##*-}" in \
        amd64) rustArch='x86_64-unknown-linux-gnu'; rustupSha256='ed7773edaf1d289656bdec2aacad12413b38ad0193fff54b2231f5140a4b07c5' ;; \
        armhf) rustArch='armv7-unknown-linux-gnueabihf'; rustupSha256='7a7b9d246ad63358705d8d4a7d5c2ef1adfec24525d1d5c44a7739e1b867e84d' ;; \
        arm64) rustArch='aarch64-unknown-linux-gnu'; rustupSha256='f80a0a792b3ab905ab4919474daf4d3f60e574fc6987e69bfba2fd877241a8de' ;; \
        i386) rustArch='i686-unknown-linux-gnu'; rustupSha256='4473c18286aa1831683a772706d9a5c98b87a61cc014d38063e00a63a480afef' ;; \
        *) echo >&2 "unsupported architecture: ${dpkgArch}"; exit 1 ;; \
    esac && \
    rustup_url="https://static.rust-lang.org/rustup/archive/1.23.1/${rustArch}/rustup-init" && \
    wget "$rustup_url" && \
    echo "${rustupSha256} *rustup-init" | sha256sum -c - && \
    chmod +x rustup-init && \
    ./rustup-init -y --no-modify-path --profile minimal --default-toolchain $RUST_VERSION --default-host ${rustArch} && \
    rm rustup-init && \
    chmod -R a+w $RUSTUP_HOME $CARGO_HOME && \
    rustup --version && \
    cargo --version && \
    rustc --version && \
    # do this symlink for numpy
    ln -s /usr/include/locale.h /usr/include/xlocale.h && \
    # update pip, install Cython, pytest, youtube-dl
    pip install -U pip Cython pytest youtube-dl -q --retries 30 && \
    # remove caches
    rm -rf /root/.cache/pip/* && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    find /usr/local -depth \
        \( \
            \( -type d -a \( -name test -o -name tests \) \) \
            -o \
            \( -type f -a \( -name '*.pyc' -o -name '*.pyo' \) \) \
        \) -exec rm -rf '{}' +


RUN apt-get update \
    && apt-get install -qq -y --no-install-recommends \
    gcc \
    python3-dev \
    python3-opencv \
    python3-wxgtk4.0 \
    python3-pip \
    python3-matplotlib \
    python3-lxml \
    python3-pygame \
    python3-cffi \
    libavdevice-dev \
    libavfilter-dev \
    libopus-dev \
    libvpx-dev \ 
    pkg-config \
    build-essential \
    libssl-dev \
    libffi-dev \
    libxml2 \
    libxslt-dev \
    libsrtp2-dev \
    zlib1g-dev \
    udev

RUN printf '#!/bin/sh\nexit 0' > /usr/sbin/policy-rc.d

RUN apt-get install -y --no-install-recommends \
    dbus \
    bluez \
    bluetooth \
    cmake \
    ninja-build \
    patchelf \
    autoconf \
    automake \
    libglib2.0-dev \
    libgirepository1.0-dev \
    libcairo2-dev \
    gir1.2-gtk-3.0

RUN pip install --upgrade pip

COPY ./requirements.txt ./

RUN python -m pip install  --no-cache-dir --user -r requirements.txt

FROM $base_image
COPY --from=0 /root/.local /root/.local

WORKDIR  /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH=/root/.local/bin:$PATH

RUN printf '#!/bin/sh\nexit 0' > /usr/sbin/policy-rc.d

RUN apt-get update \
    && apt-get install -qq -y --no-install-recommends \
    ffmpeg \
    libsrtp2-dev \
    dbus \
    bluez \ 
    bluetooth \
    python3-gi \
    git
    #installying python3-gi unfortunately brings along python3.9 -- for some reason
    #python3-gi doesn't want to accept the installed python3.10
    #There is likely some clean way to get the gi libs without bringing in this
    #extra python, but I'm over toying around with it.

COPY src/ .

# Copy the entrypoint script into the container
COPY entrypoint.sh /usr/local/bin/

# Make the entrypoint script executable
RUN chmod +x /usr/local/bin/entrypoint.sh

# Set the entrypoint script to be executed
ENTRYPOINT ["entrypoint.sh"]
