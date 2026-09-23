${OTEL_HOSTNAME} {
  redir /loadgen /loadgen/ 308

  handle_path /loadgen/* {
    reverse_proxy load-generator:8089
  }

  handle /feature {
    rewrite * /
    reverse_proxy flagd-ui:4000
  }

  handle_path /feature/* {
    reverse_proxy flagd-ui:4000
  }

  handle /featurelive/* {
    uri replace /featurelive/ /live/
    reverse_proxy flagd-ui:4000
  }

  handle_path /flagservice/* {
    reverse_proxy flagd:8013
  }

  reverse_proxy frontend-proxy:8080
}
