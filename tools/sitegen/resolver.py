"""w3id.org-style Apache .htaccess that resolves vocabulary IRIs to site pages / RDF."""
from __future__ import annotations

from .config import Config


def htaccess(cfg: Config, term_rdf: bool) -> str:
    r = cfg.section("resolver")
    site = cfg.site_url
    slug = r.get("slug_pattern", "[^/]+")
    scheme_iri = cfg.vocab.get("scheme_iri") or cfg.namespace
    local = scheme_iri[len(cfg.namespace):] if scheme_iri.startswith(cfg.namespace) else ""
    root_pat = f"^({local})?$" if local else "^$"
    whole_ttl = whole_jsonld = None
    for d in cfg.vocab.get("downloads") or []:
        name = d["path"].rsplit("/", 1)[-1]
        if name.endswith(".ttl") and not whole_ttl:
            whole_ttl = f"{site}/downloads/{name}"
        if name.endswith((".jsonld", ".json")) and not whole_jsonld:
            whole_jsonld = f"{site}/downloads/{name}"

    out = [
        f"# Redirects for https://w3id.org/{r.get('w3id_path', '')}/",
        f"# Generated from {cfg.path.name} by tools/sitegen — regenerate instead of editing.",
        f"# Target site: {site}/",
        "",
        "Options +FollowSymLinks",
        "RewriteEngine on",
        "",
    ]
    if term_rdf:
        out += [
            "# Explicit extension: /{id}.ttl, /{id}.jsonld",
            f"RewriteRule ^({slug})\\.(ttl|jsonld)$ {site}/term/$1.$2 [R=303,L]",
            "",
            "# Content negotiation for a term IRI",
            "RewriteCond %{HTTP_ACCEPT} text/turtle",
            f"RewriteRule ^({slug})/?$ {site}/term/$1.ttl [R=303,L]",
            "RewriteCond %{HTTP_ACCEPT} application/ld\\+json",
            f"RewriteRule ^({slug})/?$ {site}/term/$1.jsonld [R=303,L]",
            "",
        ]
    out += [
        "# Term IRI → term page (default, browsers)",
        f"RewriteRule ^({slug})/?$ {site}/term/$1/ [R=303,L]",
        "",
        "# Namespace / scheme IRI → whole vocabulary",
    ]
    if whole_ttl:
        out += ["RewriteCond %{HTTP_ACCEPT} text/turtle", f"RewriteRule {root_pat} {whole_ttl} [R=303,L]"]
    if whole_jsonld:
        out += [
            "RewriteCond %{HTTP_ACCEPT} application/ld\\+json",
            f"RewriteRule {root_pat} {whole_jsonld} [R=303,L]",
        ]
    out += [
        f"RewriteRule {root_pat} {site}/ [R=303,L]",
        "",
        "# Other local names (relation properties) → vocabulary schema page",
        f"RewriteRule ^([A-Za-z][A-Za-z0-9_-]*)$ {site}/schema/#$1 [R=303,NE,L]",
        "",
    ]
    return "\n".join(out)
