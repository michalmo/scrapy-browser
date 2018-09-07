import base64
import json
import time

from flask import Flask, Response, request
import requests


app = Flask('adapter')


def sse(event_name, data):
    """
    Output SSE format:
      https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#Event_stream_format

    :param event_name: event name that can be listened to
    :param data: anything
    """
    return "event: {}\ndata: {}\n\n".format(event_name, json.dumps(data))


def serialize_response(response):
    return {
        'url': response.url,
        'status': response.status_code,
        'headers': dict(response.headers),
        'body': base64.encodebytes(response.raw.read()).decode('ascii'),
    }


def event_generator(url):
    for i in range(1, 51):
        yield sse('response', serialize_response(requests.get(
            url
            if i == 1
            else f'http://books.toscrape.com/catalogue/page-{i}.html',
            stream=True,
        )))
        print(f'yielded response #{i}')
        time.sleep(.1)


@app.route('/render.json', methods=['POST'])
def events():
    data = request.get_json()
    return Response(event_generator(data['url']), content_type='text/event-stream')


if __name__ == '__main__':
    app.run(port=8050, threaded=True)
