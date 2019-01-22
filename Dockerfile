FROM continuumio/miniconda3:4.5.12

# Configuration required for using Binder
ENV NB_USER jovyan
ENV NB_UID 1000
ENV HOME /home/${NB_USER}

RUN adduser --disabled-password \
    --gecos "Default user" \
    --uid ${NB_UID} \
    ${NB_USER}


# Install some linux tools
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    unzip

# Install wine
RUN dpkg --add-architecture i386 \
    && apt-add-repository https://dl.winehq.org/wine-builds/ubuntu/ \
    && wget -nc https://dl.winehq.org/wine-builds/Release.key \
    && apt-key add Release.key \
    && apt-get install --install-recommends winehq-stable

# Install LAStools
RUN wget http://www.cs.unc.edu/~isenburg/lastools/download/LAStools.zip \
    -O lastools.zip \
    && unzip -q lastools.zip \
    # stuff that comes with LAStools that we don't want
    -x "LAStools/*toolbox/*" "LAStools/example*/*" "LAStools/src/*" \
    "LAStools/data/*" \
    -d ${HOME} \
    && rm lastools.zip

# Install FUSION
RUN wget http://forsys.sefs.uw.edu/Software/FUSION/fusionlatest.zip \
    -O fusion.zip \
    && unzip -q fusion.zip -x "APScripts/*" -d ${HOME}
    && rm fusion.zip


# Make sure the contents of our repo are in ${HOME}
COPY . ${HOME}
USER root
RUN chown -R ${NB_UID} ${HOME}
USER ${NB_USER}


# Set up our conda environment
COPY environment.yml /tmp/environment.yml

RUN conda config --add channels conda-forge \
    && conda env create -n pyFIRS -f /tmp/environment.yml \

RUN echo "source activate pyFIRS" > ~/.bashrc
ENV PATH /opt/conda/envs/pyFIRS/bin:$PATH

# install pyFIRS
RUN python setup.py develop

RUN pip install --no-cache-dir notebook==5.*
