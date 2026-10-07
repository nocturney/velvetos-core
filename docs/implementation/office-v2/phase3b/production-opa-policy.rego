package office.shadow

default allow := false

allow if {
  input.principal == "svc:shadow"
  input.action == "read"
  input.resource == "secret:alpha"
}

allow if {
  input.principal == "svc:officev2-p3b-pilot-publisher-snapshot"
  input.action == "publisher.snapshot.read"
  input.resource == "cloudflare:velvetos-instagram-publisher"
}

allow if {
  input.principal == "svc:officev2-p3b-prod-publisher-snapshot"
  input.action == "publisher.snapshot.read"
  input.resource == "cloudflare:velvetos-instagram-publisher"
}
