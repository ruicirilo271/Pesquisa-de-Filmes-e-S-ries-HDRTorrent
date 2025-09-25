from flask import Flask, render_template, request, send_file, redirect, url_for
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

app = Flask(__name__)

# Proxy de imagens
@app.route("/proxy")
def proxy():
    url = request.args.get("url")
    if not url:
        return send_file("static/default_cover.png")
    try:
        r = requests.get(url, stream=True, timeout=10)
        if r.status_code == 200 and 'image' in r.headers.get("Content-Type", ""):
            return r.content, 200, {"Content-Type": r.headers.get("Content-Type")}
        else:
            return send_file("static/default_cover.png")
    except:
        return send_file("static/default_cover.png")

def search_movies(query):
    filmes = []
    search_url = f"https://hdrtorrent.com/?s={quote(query)}"
    r = requests.get(search_url)
    soup = BeautifulSoup(r.text, "html.parser")
    items = soup.select(".capa-img")
    for item in items:
        link_tag = item.select_one("h2.h6 a")
        img_tag = item.select_one("img")
        if link_tag:
            title = link_tag.get_text(strip=True)
            url_f = link_tag["href"]
            img = img_tag["src"] if img_tag else url_for("static", filename="default_cover.png")

            import re
            match = re.search(r'\((\d{4})\)', title)
            ano = match.group(1) if match else ""

            qual = ""
            q_tag = item.select_one(".box_qual")
            if q_tag:
                qual = q_tag.get_text(strip=True)

            filmes.append({
                "title": title,
                "url": url_f,
                "img": img,
                "ano": ano,
                "qualidade": qual
            })
    return filmes

@app.route("/", methods=["GET", "POST"])
def index():
    query = ""
    filmes = []
    if request.method == "POST":
        query = request.form.get("query")
        if query:
            filmes = search_movies(query)
    return render_template("index.html", filmes=filmes, query=query)

@app.route("/detalhes")
def detalhes():
    url_f = request.args.get("url")
    if not url_f:
        return redirect(url_for("index"))

    r = requests.get(url_f)
    soup = BeautifulSoup(r.text, "html.parser")

    titulo_tag = soup.select_one(".post-title h1")
    titulo = titulo_tag.get_text(strip=True) if titulo_tag else "Detalhes do Filme"

    capa_tag = soup.select_one(".post-thumbnail img")
    if capa_tag and capa_tag.get("src"):
        capa_url = capa_tag.get("src")
    else:
        capa_url = url_for("static", filename="default_cover.png")
    capa = url_for('proxy') + "?url=" + capa_url

    downloads = []
    series = []

    # Captura links de filmes com qualidade
    for link in soup.select("a"):
        href = link.get("href", "")
        if "magnet:" in href:
            texto = link.get_text(strip=True) or "Download"
            qual = ""
            parent = link.parent
            if parent:
                for badge in parent.select(".badge-1080, .badge-720, .badge-CAM"):
                    qual = badge.get_text(strip=True)
            downloads.append({
                "url": href,
                "texto": texto,
                "titulo": titulo,
                "qualidade": qual
            })

    # Captura episódios de séries
    if soup.select(".episodios li"):
        temporadas = soup.select(".episodios")
        for season_tag in temporadas:
            season_title_tag = season_tag.select_one("h3")
            season_title = season_title_tag.get_text(strip=True) if season_title_tag else "Temporada"
            eps = []
            for li in season_tag.select("li"):
                ep_title_tag = li.select_one("a")
                ep_title = ep_title_tag.get_text(strip=True) if ep_title_tag else "Episódio"
                ep_downloads = []
                for link in li.select("a"):
                    href = link.get("href","")
                    if "magnet:" in href:
                        texto = link.get_text(strip=True) or "Download"
                        qual = ""
                        for badge in li.select(".badge-1080, .badge-720, .badge-CAM"):
                            qual = badge.get_text(strip=True)
                        ep_downloads.append({
                            "url": href,
                            "texto": texto,
                            "titulo": ep_title,
                            "qualidade": qual
                        })
                eps.append({"titulo": ep_title, "downloads": ep_downloads})
            series.append({"season_title": season_title, "episodes": eps})

    return render_template(
        "detalhes.html",
        titulo=titulo,
        capa=capa,
        downloads=downloads,
        series=series,
        filme=bool(downloads),
        series_exist=bool(series)
    )

if __name__ == "__main__":
    app.run(debug=True)



















