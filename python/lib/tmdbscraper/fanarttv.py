from . import api_utils
try:
    from urllib import quote
except ImportError: # py2 / py3
    from urllib.parse import quote

API_KEY = '384afe262ee0962545a752ff340e3ce4'

# Cloudflare Worker Proxy Configuration
PROXY_BASE_URL = 'https://tmdb-scraper-proxy.sharonjoseph52.workers.dev'

# Use proxy URL instead of direct API calls
API_URL = PROXY_BASE_URL + '/fanart/v3/movies/{}'

ARTMAP = {
    'movielogo': 'clearlogo',
    'hdmovielogo': 'clearlogo',
    'hdmovieclearart': 'clearart',
    'movieart': 'clearart',
    'moviedisc': 'discart',
    'moviebanner': 'banner',
    'moviethumb': 'landscape',
    'moviebackground': 'fanart',
    'movieposter': 'poster'
}

HEADERS = (
    ('User-Agent', 'Kodi Movie scraper by Team Kodi'),
    ('api-key', API_KEY),
)


def get_details(uniqueids, clientkey, language, set_tmdbid):
    media_id = _get_mediaid(uniqueids)
    if not media_id:
        return {}

    movie_data = _get_data(media_id, clientkey)
    movieset_data = _get_data(set_tmdbid, clientkey) if set_tmdbid else None
    if not movie_data and not movieset_data:
        return {}

    movie_art = {}
    movieset_art = {}
    if movie_data:
        movie_art = _parse_data(movie_data, language)
    if movieset_data:
        movieset_art = _parse_data(movieset_data, language)
        movieset_art = {'set.' + key: value for key, value in movieset_art.items()}

    available_art = movie_art
    available_art.update(movieset_art)

    return {'available_art': available_art}

def _get_mediaid(uniqueids):
    for source in ('tmdb', 'imdb', 'unknown'):
        if source in uniqueids:
            return uniqueids[source]

def _get_data(media_id, clientkey):
    headers = dict(HEADERS)
    if clientkey:
        headers['client-key'] = clientkey
    api_utils.set_headers(headers)
    fanarttv_url = API_URL.format(media_id)
    return api_utils.load_info(fanarttv_url, default={})

def _parse_data(data, language, language_fallback='en'):
    result = {}
    for arttype, artlist in data.items():
        if arttype not in ARTMAP:
            continue
        for image in artlist:
            image_lang = _get_imagelanguage(arttype, image)
            if image_lang and image_lang != language and image_lang != language_fallback:
                continue

            generaltype = ARTMAP[arttype]
            if generaltype == 'poster' and not image_lang:
                generaltype = 'keyart'
            if artlist and generaltype not in result:
                result[generaltype] = []

            url = quote(image['url'], safe="%/:=&?~#+!$,;'@()*[]")
            resultimage = {'url': url, 'preview': url.replace('.fanart.tv/fanart/', '.fanart.tv/preview/'), 'lang': image_lang}
            result[generaltype].append(resultimage)

    return result

def _get_imagelanguage(arttype, image):
    if 'lang' not in image or arttype == 'moviebackground':
        return None
    if arttype in ('movielogo', 'hdmovielogo', 'hdmovieclearart', 'movieart', 'moviebanner',
            'moviethumb', 'moviedisc'):
        return image['lang'] if image['lang'] not in ('', '00') else 'en'
    # movieposter may or may not have a title and thus need a language
    return image['lang'] if image['lang'] not in ('', '00') else None
