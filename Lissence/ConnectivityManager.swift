import Foundation
import WatchConnectivity
import Combine

// 1. 주고받을 메시지 타입 정의 (Codable)
struct MessageData: Codable {
    let title: String
    let iconName: String
    let isDanger: Bool
}

// 2. 통신 매니저 (ObservableObject -> SwiftUI 뷰에서 바로 감지 가능)
final class ConnectivityManager: NSObject, ObservableObject {
    
    static let shared = ConnectivityManager() // 싱글톤
    
    // UI가 구독할 데이터 (작성자님이 잘 쓰는 @Published)
    @Published var receivedMessage: MessageData?
    
    override private init() {
        super.init()
        // 세션 시작
        if WCSession.isSupported() {
            WCSession.default.delegate = self
            WCSession.default.activate()
        }
    }
    
    // 메시지 보내기 함수
    func send(message: MessageData) {
        guard WCSession.default.isReachable else {
            print("워치가 연결되어 있지 않음 (또는 앱이 꺼져있음)")
            return
        }
        
        // 구조체를 Dictionary로 변환하여 전송
        if let data = try? JSONEncoder().encode(message),
           let dictionary = try? JSONSerialization.jsonObject(with: data, options: []) as? [String: Any] {
            WCSession.default.sendMessage(dictionary, replyHandler: nil)
        }
    }
}

// 3. WCSession 델리게이트 (데이터 수신 처리)
extension ConnectivityManager: WCSessionDelegate {
    func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {
        // 연결 활성화 완료 시 처리
    }
    
    // (iOS 전용) 워치 앱이 설치 안 되어 있거나 할 때 등등의 필수 메서드들...
    #if os(iOS)
    func sessionDidBecomeInactive(_ session: WCSession) {}
    func sessionDidDeactivate(_ session: WCSession) {
        WCSession.default.activate() // 다시 활성화
    }
    #endif
    
    // ★ 실제 메시지를 받았을 때 호출되는 함수
    func session(_ session: WCSession, didReceiveMessage message: [String : Any]) {
        // UI 업데이트는 메인 스레드에서
        DispatchQueue.main.async {
            // 받은 Dictionary를 다시 구조체로 변환
            if let data = try? JSONSerialization.data(withJSONObject: message, options: []),
               let decodedMessage = try? JSONDecoder().decode(MessageData.self, from: data) {
                self.receivedMessage = decodedMessage
            }
        }
    }
}
