import os
import socket
import sys
from dotenv import load_dotenv


def main():
    # Accept host as CLI arg (preferred). Otherwise load from .env, otherwise default to 127.0.0.1
    if len(sys.argv) > 1 and sys.argv[1].strip():
        h = sys.argv[1].strip()
    else:
        load_dotenv()
        h = os.getenv('HOST', '127.0.0.1')
    try:
        socket.getaddrinfo(h, None)
    except Exception as e:
        print('HOST_RESOLVE_ERROR:' + str(e))
        sys.exit(1)
    print('HOST resolved: ' + h)
    sys.exit(0)


if __name__ == '__main__':
    main()
