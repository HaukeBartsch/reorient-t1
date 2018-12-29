FROM ubuntu:18.04

ARG DEBIAN_FRONTEND=noninteractive

#----------------------------------------------------------
# Install common dependencies and create default entrypoint
#----------------------------------------------------------
ENV LANG="en_US.UTF-8" \
    LC_ALL="C.UTF-8" \
    ND_ENTRYPOINT="/deap-startup.sh"

RUN apt-get update -qq && apt-get install -yq --no-install-recommends  \
        python3 \
        python3-pip \
        build-essential \
        git \
    && pip3 install pydicom numpy \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && git clone https://github.com/HaukeBartsch/reorient-t1.git /root/reorient \
    && cd /root/reorient \
    && chmod +x /root/reorient/reorient.py

ENTRYPOINT ["/root/reorient/reorient.py"]