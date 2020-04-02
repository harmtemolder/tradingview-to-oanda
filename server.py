import json
from json.decoder import JSONDecodeError
import logging
import web

logging.basicConfig(level=logging.INFO)

urls = (
    "/webhook/(.*)", "webhook",
    "/(.*)", "index",
)
app = web.application(urls, globals())

class index:
    def GET(self, path):
        logging.info("GET: Request received on {}".format(path))

        web.header("Content-Type", "text/plain")
        return web.notfound("You've reached an undefined endpoint."
                            " What exactly were you trying?")

class webhook:
    def GET(self, path):
        logging.info("GET: Request received on {}".format(path))

        web.header("Content-Type", "text/plain")
        return web.notfound("Nothing to GET here. Please POST something"
                            " instead.")

    def POST(self, path):
        post_data = web.data()

        try:
            loaded_data = json.loads(post_data)
        except JSONDecodeError:
            logging.exception("POST: Request received with invalid JSON")
            return web.internalerror("Your JSON could not be read. Was"
                                     " it even JSON?")
        else:
            logging.info("POST: Request received on webhook/{} with"
                         " JSON: {}".format(
                path,
                json.dumps(loaded_data)))

            web.header("Content-Type", "text/plain")
            return "Thanks for POSTing. Goodbye."

if __name__ == "__main__":
    app.run()
