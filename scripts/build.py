#!/usr/bin/env python3
"""Generate site/ from the raw store: the 1998 Citeweb framed redesign.

Inputs (read-only, never published as is), `$CITEWEB_RAW` or ~/Code/Citeweb/raw:
  captures/NewCTW/dialup02.ftd.fr/   Teleport Pro capture of the framed redesign (frame, sections)
  Citeweb/Site/aide/                 help pages (templates whose server include is replaced below)

Output: site/ (wiped and rebuilt, deterministic), then scripts/seo.py (robots, sitemap, frame restore).
Links that needed the server (counters, member area, webmail, forms) become plain text; other external
links are kept and open in a new window. Personal e-mail addresses are masked as local@????, role
addresses (tech@, irc@...) are kept. No engine code is copied.

Usage: python3 -I scripts/build.py
"""
import os
import posixpath
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RAW = Path(os.environ.get("CITEWEB_RAW") or Path.home() / "Code/Citeweb/raw")
CAP = RAW / "captures/NewCTW/dialup02.ftd.fr"
AIDE = RAW / "Citeweb/Site/aide"
SITE = REPO / "site"
HOST = "citeweb98.sauthier.family"

RENAME = {"milieu.htm-a.htm": "milieu.htm", "centre.htm-a.htm": "centre.htm", "depart.htm-a.htm": "depart.htm"}
SKIP_CAP = {"citeweb/index.htm", "citeweb/a.htm", "citeweb/pub.htm", "citeweb/inscription/login.htm"}
SKIP_DIRS = ("cgidll", "forums", "aide")  # help comes from Site/aide
MAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
HREF = re.compile(r'(<a\b[^>]*?)\bhref\s*=\s*(?:"([^"]*)"|\'([^\']*)\')([^>]*>)(.*?)(</a>)', re.I | re.S)
ATTR_LINK = re.compile(r'\b(href|src)\s*=\s*"([^"]*)"', re.I)
TPP = re.compile(r'\s+tppabs\s*=\s*"[^"]*"', re.I)
TOPSELF = re.compile(r"<SCRIPT[^>]*>\s*(?:<!--)?\s*if\s*\(\s*(?:top\s*==\s*self|self\s*==\s*top).*?</SCRIPT>", re.I | re.S)
FORM = re.compile(r"</?form\b[^>]*>", re.I)
INPUT = re.compile(r"<input\b[^>]*>", re.I)
SCRIPT_LOC = re.compile(r"<SCRIPT[^>]*>[^<]*parent\.\w+\.location[^<]*</SCRIPT>", re.I | re.S)

SCRIPT_IRC_MENU = re.compile(r"<script[^>]*>\s*(?:<!--)?\s*ssm = new Array\(\).*?</script>", re.I | re.S)
BOT_NAME = re.compile(r'ssm\[\d+\]\s*=\s*"([^"]+)"')
HEAD_OPEN = re.compile(r"<head[^>]*>", re.I)
HTML_OPEN = re.compile(r"<html[^>]*>", re.I)
ROBOTS_META = re.compile(r"<meta[^>]*name\s*=\s*[\"']?robots[\"']?[^>]*>", re.I)
EXTERNAL = re.compile(r"^(?:https?|ftp|news|irc)://", re.I)
# Links that need the server (counters, member area, webmail, ricochet redirect, chat settings): plain text.
SERVER_LINK = re.compile(r"/membres/|ricochet|\.ctw\b|chatcfg", re.I)
# The webmail link (citeweb.net/email) is kept as written: like a broken external link, it stays.
KEPT_AS_WRITTEN = re.compile(r"/email\b", re.I)
# Role or example addresses, not a person: kept in clear (the help pages tell the reader where to write).
ROLE_MAIL = {"tech", "login", "votrelogin", "moi", "moncopain", "webmaster2", "formulaires", "cc", "irc",
             "citeweb", "citeweb-subscribe", "citeweb-unsubscribe", "citeweb-help"}
# Data of a real visitor shipped as a sample in a help page: replaced.
VISITOR_SAMPLE = {"aide/formmail.htm": [("194.206.68.216", "????"), ("dial16.netinfo.fr", "????")]}
# Frame fragments and empty directory pages: they stay online for the frames but are not indexed
# (noindex keeps them out of the sitemap too).
NOINDEX_PAGES = {"citeweb/blanc.htm", "citeweb/centre.htm", "citeweb/depart.htm", "citeweb/gauche.htm",
                 "citeweb/gb.htm", "citeweb/gh.htm", "citeweb/haut.htm", "citeweb/milieu.htm",
                 "citeweb/pub.htm", "membres/index.htm", "sites/index.htm"}

HEADER = """<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML//EN">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<title>%(title)s - CITEWEB</title>
</head>
<body bgcolor="#FFFFFF" link="#000000" vlink="#000000" alink="#000000">
<table border="0" width="440">
    <tr>
        <td>
  <table border="0" cellpadding="0" cellspacing="0" width="100%%">
    <tr>
      <td><font size="3" face="Verdana"><strong> %(title)s </strong></font></td>
      <td align="right">
        <div align="right">
          <table border="0" cellspacing="0" bgcolor="#000000">
            <tr>
              <td>
                <table border="0" bgcolor="#C8AFF5">
                  <tr>
                    <td><font size="1" face="Verdana"><strong>%(nav)s</strong></font></td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>
        </div>
      </td>
    </tr>
  </table>
"""
FOOTER = "\n        </td>\n    </tr>\n</table>\n</body>\n</html>\n"

HOME_NOTE = """<p><font size="2" face="Verdana" color="#777777"><strong>&gt; archive</strong><br>
CITEWEB was a free web host for French-language personal sites, run by volunteers from 1996
until it was sold in 1999. This archive keeps its 1998 redesign: the framed interface, the
sign-up and hosting rules pages and the help pages (FTP, e-mail, IRC services...).</font></p>
<p><font size="2" face="Verdana" color="#777777">The original home page of this frame was not captured. The pages
that needed the server (member area, forums, member directory, search, counters and forms) are not
part of the archive.</font></p>
<p><font size="2" face="Verdana" color="#777777"><strong>&gt; the 1997 site</strong><br>
The complete 1997 CITEWEB, with the sites it hosted, is at
<a href="https://citeweb97.sauthier.family" style="color:#777777">citeweb97.sauthier.family</a>.</font></p>
"""

NOT_FOUND = """<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML//EN">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<title>404 - CITEWEB</title>
</head>
<body bgcolor="#FFFFFF" link="#000000" vlink="#000000" alink="#000000">
<table border="0" width="440">
    <tr>
        <td><p><font color="#8879B5" size="7" face="Verdana, Arial, Helvetica, sans-serif"><b>erreur 404</b></font><br>
        <font color="#8879B5" size="4" face="Verdana, Arial, Helvetica, sans-serif"><b>fichier non trouv&eacute; / file not found</b></font></p>
        <hr>
        <p><font size="2" face="Verdana"><a href="/">&gt; CITEWEB (archive)</a></font></p>
        </td>
    </tr>
</table>
</body>
</html>
"""


def read(p):
    return p.read_bytes().decode("latin-1")


def write(rel, text):
    out = SITE / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(text.encode("latin-1", "replace"))


def exists(rel):
    p = SITE / rel
    return p.is_file() or (p.is_dir() and (p / "index.htm").is_file())


def fix_link(url, page):
    """Return the rewritten URL, or None when it must become plain text."""
    u = url.strip()
    if not u or u.startswith(("#", "javascript:")):
        return u
    if u.lower().startswith("mailto:"):
        return None
    m = re.match(r"(?:https?|ftp|news|irc)://([^/?#]+)(.*)$", u, re.I)
    if m:
        host, rest = m.group(1).lower(), m.group(2)
        if host not in ("citeweb.net", "www.citeweb.net"):
            return u  # another site, alive or dead: kept as written in the original
        if KEPT_AS_WRITTEN.search(rest):
            return u
        if SERVER_LINK.search(rest):
            return None
        u = rest or "/"
    path, _, frag = u.partition("#")
    path = path.split("?")[0]
    path = posixpath.normpath(path if path.startswith("/") else posixpath.join(posixpath.dirname("/" + page), path))
    rel = path.lstrip("/").lower()
    if rel.rstrip("/") == "":
        return "/index.htm"
    if not exists(rel.rstrip("/")):
        return None
    if (SITE / rel.rstrip("/")).is_dir():
        rel = rel.rstrip("/") + "/index.htm"
    return "/" + rel + ("#" + frag if frag else "")


def blank(tag):
    """External links open in a new window, so that the frames stay in place (tag ends with '>')."""
    tag = re.sub(r'\s+(?:target|rel)\s*=\s*(?:"[^"]*"|\'[^\']*\'|[^\s>]+)', "", tag, flags=re.I)
    return tag[:-1] + ' target="_blank" rel="noopener">'


def irc_menu(text):
    """The bot list was written by a script whose form button is gone: plain links instead."""
    names = BOT_NAME.findall(text)
    links = "".join('<p align="center"><a href="%s.htm">%s</a></p>\n' % (n.lower(), n) for n in names)
    return SCRIPT_IRC_MENU.sub(lambda _: links, text, count=1)


def head_meta(text, page):
    """Charset and robots meta where missing (the server sends text/html only, pages are Latin-1)."""
    extra = ""
    if "charset" not in text[:4096].lower():
        extra += '<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">'
    if page in NOINDEX_PAGES:  # replaces any robots meta of the capture
        text = ROBOTS_META.sub("", text)
        extra += '<meta name="robots" content="noindex">'
    if not extra:
        return text
    m = HEAD_OPEN.search(text) or HTML_OPEN.search(text)
    if m:
        return text[:m.end()] + extra + text[m.end():]
    return extra + text


def clean(text, page):
    text = TPP.sub("", text)
    text = TOPSELF.sub("", text)
    text = SCRIPT_LOC.sub("", text)
    if page.startswith("aide/irc/"):
        text = irc_menu(text)
    if page == "aide/index.htm":  # the IRC services help was reachable only from the bot menu
        text = text.replace('<a href="irc.htm"', '<a href="/aide/irc/index.htm" target="_blank" rel="noopener">services IRC (bots de service)</a><br>\n          <a href="irc.htm"', 1)
    text = FORM.sub("", text)
    text = INPUT.sub("", text)
    for old, new in VISITOR_SAMPLE.get(page, []):
        text = text.replace(old, new)

    def anchor(m):
        url = m.group(2) if m.group(2) is not None else m.group(3)
        new = fix_link(url, page)
        if new is None:
            return m.group(5)
        tag = '%shref="%s"%s' % (m.group(1), new, m.group(4))
        if EXTERNAL.match(new):
            tag = blank(tag)
        return tag + m.group(5) + m.group(6)

    text = HREF.sub(anchor, text)
    # frameset sources, images, image maps
    text = re.sub(r'(\bsrc\s*=\s*")([^"]*)(")', lambda m: m.group(1) + RENAME.get(m.group(2), m.group(2)) + m.group(3), text, flags=re.I)

    def area(m):
        new = fix_link(m.group(2), page)
        if new is None:
            return ""
        tag = m.group(1) + new + m.group(3)
        return blank(tag) if EXTERNAL.match(new) else tag

    text = re.sub(r'(<area\b[^>]*?\bhref\s*=\s*")([^"]*)("[^>]*>)', area, text, flags=re.I)
    text = re.sub(r'(<area\b[^>]*?)\s+target\s*=\s*"centre"', r"\1", text, flags=re.I)

    def mail(m):
        local = m.group(0).split("@")[0]
        return m.group(0) if local.lower() in ROLE_MAIL else local + "@????"

    text = MAIL.sub(mail, text)
    return head_meta(text, page)


def build():
    if SITE.exists():
        shutil.rmtree(SITE)
    pages = []  # (rel, text) written after all files exist, so links can be checked

    # 1. frame capture
    for f in sorted(CAP.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(CAP).as_posix()
        if rel in SKIP_CAP or rel.split("/")[0] in SKIP_DIRS or f.suffix.lower() == ".exe":
            continue
        rel = posixpath.join(posixpath.dirname(rel), RENAME.get(f.name, f.name))
        if f.suffix.lower() in (".htm", ".html"):
            pages.append((rel, read(f)))
        else:
            (SITE / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(f, SITE / rel)
    (SITE / "aide").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(CAP / "aide/blanc.gif", SITE / "aide/blanc.gif")

    # 2. help pages: the server include (page header) becomes a static header
    for f in sorted(AIDE.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(AIDE).as_posix().lower()
        if rel.startswith("hist/") or rel == "irc.htm" or f.suffix.lower() in (".bak", ".ht~") or "copy of" in rel:
            continue
        out = "aide/" + rel
        if f.suffix.lower() == ".htm":
            text = read(f)
            if "<!-- #include" in text:
                m = re.search(r"<i>(?:<font>)?([^<]+)", text)
                title = " ".join(m.group(1).split()).capitalize() if m else "Aide"
                nav = '<a href="/citeweb/a.htm">&lt; page principale</a> / <a href="/aide/index.htm">aide</a>' \
                    if rel != "index.htm" else '<a href="/citeweb/a.htm">&lt; page principale</a>'
                text = re.sub(r"<!--\s*#include[^>]*aidehaut\.inc[\x22]?\s*-->",
                              lambda _: HEADER % {"title": "Aide", "nav": nav}, text, count=1)
                text = re.sub(r"<!--\s*#include[^>]*aidebas\.inc[\x22]?\s*-->", FOOTER, text)
            pages.append((out, text))
        elif f.suffix.lower() == ".gif":
            (SITE / out).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(f, SITE / out)

    # 3. new pages
    pages.append(("index.htm", """<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML//EN">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<meta name="DESCRIPTION" content="CITEWEB - votre espace d'expression sur internet (1998 archive)">
<title>CITEWEB - votre espace d'expression sur internet</title>
</head>
<frameset cols="*,620,*" border="0" framespacing="0" frameborder="no">
    <frame src="citeweb/blanc.htm" name="blanc1" scrolling="no" marginheight="0" marginwidth="0" noresize>
    <frame src="citeweb/milieu.htm" name="milieu" scrolling="no" marginheight="0" marginwidth="0" noresize>
    <frame src="citeweb/blanc.htm" name="blanc2" scrolling="no" marginheight="0" marginwidth="0" noresize>
    <noframes>
    <body><p><a href="citeweb/a.htm">CITEWEB (archive)</a></p></body>
    </noframes>
</frameset>
</html>
"""))
    for i, (rel, text) in enumerate(pages):  # the search form is gone: drop its label
        if rel == "citeweb/gh.htm":
            pages[i] = (rel, re.sub(r"<p><font[^>]*><strong>&gt;\s*rechercher sur CITEWEB<br>.*?</p>", "", text, flags=re.S))
    pages.append(("citeweb/a.htm", (HEADER % {"title": "CITEWEB (archive)", "nav": "1998"}).replace('<font size="3" face="Verdana">', '<font size="3" face="Verdana" color="#777777">') + HOME_NOTE + FOOTER))
    pages.append(("citeweb/pub.htm", '<body bgcolor="#FFFFFF"></body>\n'))
    pages.append(("404.html", NOT_FOUND))

    # Pass 1 registers every page so links can be checked, pass 2 rewrites them.
    for rel, text in pages:
        write(rel, text)
    for rel, text in pages:
        if rel not in ("404.html",):
            write(rel, clean(text, rel))

    subprocess.run([sys.executable, "-I", str(REPO / "scripts/seo.py")], check=True)


if __name__ == "__main__":
    build()
