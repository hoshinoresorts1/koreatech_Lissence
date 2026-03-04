import SwiftUI

struct iPhoneContentView: View {
    @StateObject var speechManager = SpeechManager() // 매니저 연결
    @StateObject var connectivity = ConnectivityManager.shared
    
    var body: some View {
        VStack(spacing: 30) {
            Text("음성 인식 테스트")
                .font(.title)
            
            // 변환된 텍스트가 실시간으로 보입니다.
            ScrollView {
                Text(speechManager.transcript)
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(Color.gray.opacity(0.1))
                    .cornerRadius(10)
            }
            .frame(height: 200)

            // 버튼을 누르면 녹음 시작/중지
            Button(action: {
                if speechManager.isRecording {
                    speechManager.stopRecording()
                } else {
                    speechManager.startRecording()
                }
            }) {
                Text(speechManager.isRecording ? "중지하기" : "말하기 시작")
                    .padding()
                    .background(speechManager.isRecording ? Color.red : Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
            }
            
            // 워치로 결과 보내기 테스트
            Button("이 내용을 워치로 전송") {
                let msg = MessageData(title: speechManager.transcript, iconName: "bubble.left.fill", isDanger: false)
                connectivity.send(message: msg)
            }
            .disabled(speechManager.transcript.isEmpty)
        }
        .padding()
    }
}
