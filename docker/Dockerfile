# trunk-ignore(checkov/CKV_DOCKER_2)
# trunk-ignore-all(trivy/DS026)
FROM python:3.11.8-alpine3.19 as builder

# set work directory
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install psycopg2 dependencies
# trunk-ignore(trivy/DS025)
# trunk-ignore(hadolint/DL3018)
RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev g++ libffi-dev cairo-dev


# install dependencies
COPY requirements.txt ./
RUN python -m pip install -r requirements.txt

#########
# FINAL #
#########

# pull official base image
FROM python:3.11.8-alpine3.19

# create directory for the app user
RUN mkdir -p /home/app

# create the app user
RUN addgroup -S app && adduser -S app -G app

# create the appropriate directories
ENV APP_HOME=/app
RUN mkdir $APP_HOME
WORKDIR $APP_HOME

# install dependencies
RUN apk update && apk add libpq libffi-dev build-base libffi
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

# copy project

WORKDIR ${APP_HOME}
COPY . ${APP_HOME}
# chown all the files to the app user
RUN chown -R app:app $APP_HOME
# change to the app user
USER app
WORKDIR ${APP_HOME}
