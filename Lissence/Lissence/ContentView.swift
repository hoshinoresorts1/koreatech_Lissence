// iPhone 쪽 ContentView.swift

//
//struct ContentView: View {
//    var body: some View {
//        VStack {//            Image(systemName: "globe")
//                .imageScale(.large)
//                .foregroundStyle(.tint)
//            Text("Hello, world!")
//        }
//        .padding()
//    }
//}
//
//#Preview {
//    ContentView()
//}

import SwiftUI

struct ContentView: View {
    // 통신 매니저 연결
    @StateObject var connectivity = ConnectivityManager.shared
    
    var body: some View {
        VStack(spacing: 20) {
            Button("🚨 사이렌 데이터 전송") {
                let msg = MessageData(title: "사이렌 감지!", iconName: "siren.fill", isDanger: true)
                connectivity.send(message: msg)
            }
            .buttonStyle(.borderedProminent)
            
            Button("🎵 음악 데이터 전송") {
                let msg = MessageData(title: "음악 모드", iconName: "music.note", isDanger: false)
                connectivity.send(message: msg)
            }
        }
    }
}

//#Preview {
//    ContentView()
//}
