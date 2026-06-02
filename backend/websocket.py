from fastapi import WebSocket


class ConnectionManager:

    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        """
        Acepta una nueva conexión WebSocket
        """
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Elimina una conexión cuando un jugador sale
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(
        self,
        message: str,
        websocket: WebSocket
    ):
        """
        Envía mensaje a un solo usuario
        """
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        """
        Envía mensaje a todos los usuarios conectados
        """

        disconnected = []

        for connection in self.active_connections:

            try:
                await connection.send_text(message)

            except Exception:
                disconnected.append(connection)

        for connection in disconnected:

            if connection in self.active_connections:
                self.active_connections.remove(connection)

    def total_connections(self):
        """
        Devuelve cantidad de jugadores conectados
        """
        return len(self.active_connections)


# Instancia global
manager = ConnectionManager()