# overlay: pixi for different architectures
# initial version https://www.fz-juelich.de/de/blogs/programmiere/lokale-ki-gestuetzte-pdf-verarbeitung-vibepod-pi-lm-studio-und-pixi
#
# FROM-less Dockerfile fragment; VibePod prepends the base image's `FROM <image>`

ENV PIXI_HOME=/opt/pixi

# Download pixi binaries + official SHA256 checksums via Docker ADD (no curl/wget
# needed, so this also works on minimal base images).
#
# Both linux-aarch64 and linux-64 are fetched: ADD cannot branch on the build
# architecture (BuildKit's TARGETARCH says arm64/amd64, while pixi's release
# assets are named aarch64/x86_64, and a FROM-less fragment cannot use a helper
# stage to translate). The RUN below picks the matching tarball and deletes the
# other, so the extra ~32 MB is download-only and never lands in a layer.
ADD https://github.com/prefix-dev/pixi/releases/latest/download/pixi-aarch64-unknown-linux-musl.tar.gz /tmp/pixi-aarch64.tar.gz
ADD https://github.com/prefix-dev/pixi/releases/latest/download/pixi-aarch64-unknown-linux-musl.tar.gz.sha256 /tmp/pixi-aarch64.sha256
ADD https://github.com/prefix-dev/pixi/releases/latest/download/pixi-x86_64-unknown-linux-musl.tar.gz /tmp/pixi-x86_64.tar.gz
ADD https://github.com/prefix-dev/pixi/releases/latest/download/pixi-x86_64-unknown-linux-musl.tar.gz.sha256 /tmp/pixi-x86_64.sha256

# Verify the checksum of this architecture's tarball with sha256sum -c, then
# extract it to $PIXI_HOME/bin. An unrecognised `uname -m` aborts the build
# rather than producing an image without pixi.
RUN set -ex && \
cd /tmp && \
case "$(uname -m)" in \
  aarch64|arm64) PIXI_ARCH=aarch64 ;; \
  x86_64|amd64)  PIXI_ARCH=x86_64 ;; \
  *) echo "unsupported architecture: $(uname -m)" >&2; exit 1 ;; \
esac && \
sed "s|pixi-${PIXI_ARCH}-unknown-linux-musl.tar.gz|/tmp/pixi-${PIXI_ARCH}.tar.gz|g" \
    "pixi-${PIXI_ARCH}.sha256" | sha256sum -c - && \
mkdir -p ${PIXI_HOME}/bin && \
tar xzf "/tmp/pixi-${PIXI_ARCH}.tar.gz" -C ${PIXI_HOME}/bin && \
chmod +x ${PIXI_HOME}/bin/pixi && \
rm -f /tmp/pixi-aarch64.tar.gz /tmp/pixi-aarch64.sha256 \
      /tmp/pixi-x86_64.tar.gz /tmp/pixi-x86_64.sha256

ENV PATH=/opt/pixi/bin:$PATH
RUN pixi --version

# Create vp_pixi project at /opt/vp_pixi (/opt to avoid overwriting user pixi installations)
RUN mkdir -p /opt/vp_pixi
WORKDIR /opt/vp_pixi
RUN pixi init

ENV PATH=/opt/vp_pixi/.pixi/envs/default/bin:$PATH

# Idea from Claude to use RUN to change the config.toml
# Keep workspace environments off the bind-mounted `.pixi`, which the host may
# have populated for a different platform (e.g. macOS arm64 Mach-O binaries).
# The directory is named after `uname -m`, so each architecture gets its own
# tree (/workspace/.pixi-linux-aarch64, /workspace/.pixi-linux-x86_64) and a
# workspace shared between an aarch64 and a linux-64 container never mixes them.
# `detached-environments` only accepts an absolute path, so this relies on the
# workspace being mounted at /workspace. A bad value makes pixi fall back to
# `.pixi` after printing an error, so the build echoes what it wrote.
RUN printf 'detached-environments = "/workspace/.pixi-linux-%s"\n' "$(uname -m)" \
    > ${PIXI_HOME}/config.toml && \
    cat ${PIXI_HOME}/config.toml
