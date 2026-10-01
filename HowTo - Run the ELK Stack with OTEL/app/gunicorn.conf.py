# gunicorn runs the app in pre-forked worker processes. The app module (and with it the OpenTelemetry
# SDK: exporters, background threads) is imported *inside* each worker, i.e. after the fork -- do not
# enable 'preload_app', the exporter threads would not survive the fork.
bind = "0.0.0.0:8000"
workers = 2
threads = 4
accesslog = "-"
