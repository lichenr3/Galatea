import { type WebBaseMessage, WebMessageType } from '../types/protocol';
import config from '../config';

type MessageCallback = (msg: WebBaseMessage) => void;
type StatusCallback = (isConnected: boolean) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string = config.WS_URL;
  private heartbeatTimer: number | undefined;

  // 连接函数
  connect(onMessage: MessageCallback, onStatusChange: StatusCallback) {
    // 如果已经连接，就不要重复连
    if (this.ws && this.ws.readyState === WebSocket.OPEN) return;

    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log("🔥 WS Connected");
      onStatusChange(true);
      this.startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      try {
        console.log('📨 收到原始 WebSocket 数据:', event.data);
        const msg: WebBaseMessage = JSON.parse(event.data);
        console.log('📨 解析后的消息:', msg);
        
        // 如果是心跳包回应，忽略即可，不用传给上层
        if (msg.type === WebMessageType.HEARTBEAT) {
          console.log('💓 收到心跳回应');
          return;
        }
        
        // 把消息传给回调函数
        console.log('📤 传递消息给 handleServerMessage');
        onMessage(msg);
      } catch (e) {
        console.error("❌ WS Parse Error:", e, '原始数据:', event.data);
      }
    };

    this.ws.onclose = () => {
      console.log("🔌 WS Disconnected");
      onStatusChange(false);
      this.stopHeartbeat();
    };

    this.ws.onerror = (err) => {
      console.error("WS Error:", err);
      onStatusChange(false);
    };
  }

  // 发送消息
  sendMessage(msg: WebBaseMessage) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('📡 WebSocket 发送消息:', msg);
      this.ws.send(JSON.stringify(msg));
    } else {
      console.warn("⚠️ WS 未连接，消息被丢弃:", msg);
    }
  }

  // 断开连接
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.stopHeartbeat();
  }

  // --- 心跳保活机制 ---
  private startHeartbeat() {
    this.stopHeartbeat(); // 先清理旧的
    // 每 30 秒发一次心跳
    this.heartbeatTimer = setInterval(() => {
      this.sendMessage({
        type: WebMessageType.HEARTBEAT,
        session_id: "",
        data: {},
        timestamp: Date.now() / 1000
      });
    }, 30000);
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = undefined;
    }
  }
}

// 导出单例，这样整个 App 共享同一个连接
export const webSocketService = new WebSocketService();