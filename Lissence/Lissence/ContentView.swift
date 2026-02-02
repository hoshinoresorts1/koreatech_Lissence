import SwiftUI

struct ContentView: View {
    // @StateObject: 위에서 만든 매니저를 감시하겠다는 선언입니다.
    @StateObject var connectivity = ConnectivityManager.shared
    
    // body: UIKit의 loadView()나 draw()처럼 화면을 그리는 부분입니다.
    var body: some View {
        VStack(spacing: 30) { // UIStackView(axis: .vertical)와 같습니다.
            
            // 삼항 연산자로 데이터 유무에 따라 텍스트를 바꿉니다.
            Text(connectivity.receivedMessage == nil ? "연결 대기 중" : "데이터 수신됨!")
                .font(.caption)
                .foregroundColor(.secondary)

            // 버튼 생성 (UIButton + addTarget을 합친 형태)
            Button(action: {
                let msg = MessageData(title: "사이렌 감지!", iconName: "bell.and.waves.left.and.right.fill", isDanger: true)
                
                connectivity.send(message: msg) // 1. 워치로 데이터 전송
                connectivity.receivedMessage = msg // 2. 내 화면도 업데이트
            }) {
                // 버튼의 겉모습 디자인
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
            
            // ... 이하 동일한 구조의 버튼
        }
    }
}
