from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

app = FastAPI()

clients = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received from client: {data}")
            # Respond with simulated sensor data
            await websocket.send_text(f"Hello, {data}! Here's some sensor data: 42")
    except WebSocketDisconnect:
        print("Client disconnected")
        clients.remove(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=12000)  # Port matches client connection

