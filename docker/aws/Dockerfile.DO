FROM jupyter/base-notebook:ubuntu-22.04 AS base
RUN pip3 install --no-cache-dir "web3<7.0.0" python-dotenv hpke dill

FROM base AS app
WORKDIR /app

# Copy entire project to /app
COPY --chown=1000:100 . /app
COPY --chown=1000:100 sample /app/origin-sample
RUN ls -alFh /app

# Clean up unnecessary folders
RUN rm -rf /app/docker /app/script

# Remove all files that start with '_da_'
RUN find /app -maxdepth 2 -type f -name '*_da_*' -delete

# Remove README-DA.md if present
RUN rm -rf /app/README-DA.md

# Copy and set up entrypoint
COPY --chown=1000:100 docker/aws/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
