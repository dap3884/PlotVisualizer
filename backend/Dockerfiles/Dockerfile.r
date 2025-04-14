FROM r-base:latest

# Install system dependencies for rendering, htmlwidgets, and 3D (optional)
RUN apt-get update && apt-get install -y \
    libx11-dev \
    libglu1-mesa-dev \
    xvfb \
    pandoc \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    && apt-get clean

# Install required R packages
RUN R -e "install.packages(c('plotly', 'htmlwidgets', 'ggplot2'), repos='http://cran.us.r-project.org')"

# Optional: Install rgl if you want 3D via rgl + Xvfb
RUN R -e "install.packages('rgl', repos='http://cran.us.r-project.org')"

# Create working directories
WORKDIR /scripts

# Default command to run the user script
CMD ["bash", "-c", "cd /output && Rscript /scripts/script.R"]
