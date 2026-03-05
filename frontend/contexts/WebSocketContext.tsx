import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';

type IpoUpdates = {
    [ipoId: number]: any;
};

interface WebSocketContextType {
    updates: IpoUpdates;
    connected: boolean;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export function WebSocketProvider({ children }: { children: ReactNode }) {
    const [updates, setUpdates] = useState<IpoUpdates>({});
    const [connected, setConnected] = useState(false);

    useEffect(() => {
        let ws: WebSocket | null = null;
        let reconnectTimeout: NodeJS.Timeout;

        const connect = () => {
            const wsUrl = process.env.NEXT_PUBLIC_API_BASE_URL
                ? process.env.NEXT_PUBLIC_API_BASE_URL.replace('http', 'ws') + '/ws/ipos'
                : 'ws://localhost:8000/api/v1/ws/ipos';

            ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                console.log("WebSocket connected to live IPO feed");
                setConnected(true);
            };

            ws.onclose = () => {
                setConnected(false);
                // Attempt to reconnect after 5 seconds
                reconnectTimeout = setTimeout(connect, 5000);
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.ipo_id) {
                        setUpdates(prev => ({
                            ...prev,
                            [data.ipo_id]: {
                                ...(prev[data.ipo_id] || {}),
                                ...data,
                                _timestamp: Date.now() // Force a re-render trigger for UI animations
                            }
                        }));
                    }
                } catch (e) {
                    console.error("Failed to parse websocket message", e);
                }
            };
        };

        connect();

        return () => {
            clearTimeout(reconnectTimeout);
            if (ws) ws.close();
        };
    }, []);

    return (
        <WebSocketContext.Provider value={{ updates, connected }}>
            {children}
        </WebSocketContext.Provider>
    );
}

export function useWebSocket() {
    const context = useContext(WebSocketContext);
    if (context === undefined) {
        throw new Error('useWebSocket must be used within a WebSocketProvider');
    }
    return context;
}
