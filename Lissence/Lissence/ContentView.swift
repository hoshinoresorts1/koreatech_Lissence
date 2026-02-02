import SwiftUI

struct ContentView: View {
    @StateObject var connectivity = ConnectivityManager.shared
    
    var body: some View {
        VStack(spacing: 30) {
            // 연결 상태 확인용 텍스트
            Text(connectivity.receivedMessage == nil ? "연결 대기 중" : "데이터 수신됨!")
                .font(.caption)
                .foregroundColor(.secondary)

            Button(action: {
                let msg = MessageData(title: "사이렌 감지!", iconName: "bell.and.waves.left.and.right.fill", isDanger: true)
            
                connectivity.send(message: msg) // 워치로 보냄
                connectivity.receivedMessage = msg
                
                print("아이폰: 데이터 전송 및 내 상태 업데이트 완료")
            }) {
                Label("사이렌 전송", systemImage: "bell.fill")
                    .font(.headline)
                    .padding()
                    .background(Color.red)
                    .foregroundColor(.white)
                    .cornerRadius(10)
            }
            
            Button(action: {
                let msg = MessageData(title: "음악 모드", iconName: "music.note", isDanger: false)
                connectivity.send(message: msg)
                print("아이폰: 음악 데이터 전송 버튼 눌림")
            }) {
                Label("음악 전송", systemImage: "music.note")
                    .font(.headline)
                    .padding()
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
            }
        }
    }
}
