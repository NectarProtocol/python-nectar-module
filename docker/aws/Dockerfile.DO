FROM jupyter/base-notebook:ubuntu-22.04
WORKDIR /app

COPY --chown=1000:100 . /app
RUN ls -alFh /app

# Remove docker folder
RUN rm -rf /app/docker /app/script
RUN pip3 install --no-cache-dir "web3<7.0.0" python-dotenv hpke dill

# Remove all files that start with '_da_'
RUN find /app -maxdepth 1 -type f -name '*_da_*' -delete

# Prepare README.md file
RUN rm -rf /app/README-DA.md

COPY --chown=1000:100 docker/aws/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]

