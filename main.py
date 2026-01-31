import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="NoSQL DB Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to run on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--node-id", type=str, default="0", help="Unique ID for this node")
    parser.add_argument("--peers", type=str, default="", help="Comma-separated list of peer URLs (e.g. http://localhost:8001,http://localhost:8002)")
    args = parser.parse_args()

    import os
    os.environ["DB_PORT"] = str(args.port)
    os.environ["DB_NODE_ID"] = args.node_id
    os.environ["DB_PEERS"] = args.peers

    # Import app AFTER setting environment variables
    from src.db.server import app
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
