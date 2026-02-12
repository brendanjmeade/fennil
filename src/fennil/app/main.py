from .core2 import FennilApp


def main(server=None, **kwargs):
    app = FennilApp(server)
    app.server.start(**kwargs)


if __name__ == "__main__":
    main()
